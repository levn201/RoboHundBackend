# Auftrag für Claude Code: Phase 2 – Flask Backend „Watchdog"

## Kontext

Ich baue ein Personenerkennungssystem auf einem Raspberry Pi 5 mit USB-Kamera (Logitech C920). Phase 1 (Kamera + YOLOv8n-Erkennung) läuft bereits erfolgreich als Standalone-Script `live_detection.py` im Projektordner `~/watchdog`. Jetzt soll das in eine ordentliche Flask-App-Struktur überführt werden.

**Wichtig: Die Erkennungslogik aus `live_detection.py` ist bereits getestet und funktioniert. Diese Logik soll übernommen und in die neue Struktur integriert werden, nicht neu erfunden werden.** Die Datei liegt im Projektordner, bitte zuerst lesen.

## Ziel dieser Phase

Eine Flask-App, die im Hintergrund Kamera-Capture und Personenerkennung als Threads laufen lässt, Events in SQLite speichert und über eine JSON-API abfragbar macht. **Kein Frontend in dieser Phase** – nur Backend + API. Kein Live-Stream in dieser Phase (kommt in Phase 3). Kein GPS in dieser Phase (Dummy-Werte reichen).

## Geforderte Projektstruktur

```
watchdog/
├── app/
│   ├── __init__.py      # Flask App Factory
│   ├── camera.py        # Capture-Thread + Frame-Buffer
│   ├── detector.py       # Detection-Thread (Logik aus live_detection.py übernehmen)
│   ├── gps.py            # GPS-Reader, Dummy-Implementierung
│   ├── routes.py         # API-Routen
│   └── models.py         # SQLite Setup + Event-Model
├── snapshots/             # existiert bereits, weiter nutzen
├── config.py              # zentrale Konfiguration
├── requirements.txt
└── run.py                 # Einstiegspunkt
```

## Detailanforderungen je Datei

### `config.py`
Zentrale Konstanten, aktuell hart im Script `live_detection.py` verteilt. Mindestens:
- `CAMERA_INDEX = 0`
- `DETECTION_INTERVAL = 0.4`
- `SESSION_END_BUFFER = 5.0`
- `CONFIDENCE_THRESHOLD = 0.5`
- `SNAPSHOT_DIR = "snapshots"`
- `DATABASE_PATH = "watchdog.db"`
- `FRAME_WIDTH = 1280`, `FRAME_HEIGHT = 720`

### `app/camera.py`
- Klasse `CameraStream`, die die Kamera **einmalig** öffnet (`cv2.VideoCapture`)
- Läuft in eigenem Thread, liest kontinuierlich Frames
- Hält den **aktuellsten Frame** in einem Buffer (mit `threading.Lock`, damit Detection-Thread und später Stream-Route sicher lesen können)
- Methode `get_frame()` gibt eine Kopie des aktuellen Frames zurück
- Sauberes Stoppen über `stop()`-Methode möglich (Thread beenden, `cap.release()`)
- **Wichtig:** Kamera darf nur EINMAL im ganzen Prozess geöffnet werden. Andere Module dürfen NICHT selbst `cv2.VideoCapture` aufrufen, sondern nur über diese Klasse gehen.

### `app/detector.py`
- Übernimmt die **bereits getestete Zustandslogik** aus `live_detection.py`:
  - YOLOv8n laden (`ultralytics`), nur Klasse `person` (COCO class 0)
  - Alle `DETECTION_INTERVAL` Sekunden einen Frame von `CameraStream` holen und analysieren
  - Zustandsbasierte Session-Erkennung: neue Session bei "keine Person → Person"-Wechsel, Session-Ende erst nach `SESSION_END_BUFFER` Sekunden ohne Erkennung (Puffer gegen kurze Verdeckungen)
- Bei Session-Start: Snapshot mit Bounding Box speichern (Dateiname: `{SNAPSHOT_DIR}/{timestamp}_start.jpg`), UND ein neues Event über `models.py` in die SQLite-DB schreiben
- Läuft als eigener Thread, damit der Flask-Hauptprozess nicht blockiert
- Bekommt Position von `gps.py` (`get_position()`), speichert `lat`/`lon` mit ins Event

### `app/gps.py`
- Funktion `get_position() -> tuple[float | None, float | None]`
- **Aktuell:** Dummy-Implementierung, die feste Test-Koordinaten zurückgibt (z.B. Stuttgart: `48.7758, 9.1829`)
- Interface so bauen, dass es später 1:1 durch eine echte `gpsd`-Anbindung ersetzt werden kann, ohne dass `detector.py` angepasst werden muss

### `app/models.py`
- SQLite-Verbindung und Tabellen-Setup (bei App-Start automatisch anlegen, falls nicht vorhanden)
- Tabelle `events`:
  - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  - `timestamp` (TEXT, ISO-Format)
  - `confidence` (REAL)
  - `snapshot_path` (TEXT)
  - `lat` (REAL, nullable)
  - `lon` (REAL, nullable)
  - `session_duration` (REAL, nullable – wird erst beim Session-Ende nachträglich aktualisiert, siehe unten)
- Funktionen:
  - `create_event(timestamp, confidence, snapshot_path, lat, lon) -> event_id`
  - `update_event_duration(event_id, duration)` – wird aufgerufen, wenn die Session endet
  - `get_recent_events(limit=20) -> list[dict]`
  - `get_latest_event() -> dict | None`

### `app/routes.py`
Flask Blueprint mit folgenden Routen:
- `GET /api/events` – gibt die letzten 20 Events als JSON zurück (nutzt `get_recent_events`)
- `GET /api/events/latest` – letztes Event als JSON (nutzt `get_latest_event`)
- `GET /api/status` – JSON mit: `camera_active` (bool), `detection_running` (bool), `uptime_seconds`, `last_gps_position`
- `GET /snapshots/<filename>` – liefert die Snapshot-Datei aus dem `SNAPSHOT_DIR` aus (mit `send_from_directory`, Pfad-Traversal absichern!)

Alle Responses als JSON mit sinnvollen HTTP-Statuscodes (404 falls Snapshot nicht existiert, etc.)

### `app/__init__.py`
- Flask App Factory Pattern (`create_app()`-Funktion)
- Beim App-Start: `CameraStream` und Detection-Thread initialisieren und starten
- Blueprint aus `routes.py` registrieren
- DB-Setup aus `models.py` aufrufen

### `run.py`
- Einfacher Einstiegspunkt: `from app import create_app` → `app = create_app()` → `app.run(host="0.0.0.0", port=5000, debug=False)`
- `debug=False` ist wichtig, da der Flask-Debug-Reloader sonst den Prozess doppelt startet und die Kamera zweimal geöffnet würde

### `requirements.txt`
Alle genutzten Pakete mit Versionen einfrieren (`pip freeze` im aktiven venv nutzen, dann relevante Pakete rauskopieren: `flask`, `opencv-python-headless`, `ultralytics`).

## Wichtige Randbedingungen

1. **Threading-Sicherheit:** Frame-Buffer und DB-Zugriffe müssen thread-safe sein (Locks verwenden wo nötig, insbesondere beim Frame-Buffer-Zugriff aus mehreren Threads)
2. **Keine Mehrfach-Kamera-Öffnung:** Nur `camera.py` darf `cv2.VideoCapture` aufrufen
3. **Graceful Shutdown:** Bei Strg+C oder Signal sollen Threads sauber beendet und die Kamera freigegeben werden (kein hängender Prozess, der `/dev/video0` blockiert)
4. **Bestehende Snapshots weiter nutzen:** Der `snapshots/`-Ordner existiert schon mit Testbildern, nicht löschen
5. **Kein Frontend, kein Stream, kein GPS-Hardware** in dieser Phase – nur die Grundstruktur mit Dummy-GPS

## Akzeptanzkriterien (wie ich es testen werde)

```bash
python run.py
```
soll starten und:
1. Ohne Fehler die Kamera öffnen und Detection-Thread starten
2. `curl http://localhost:5000/api/status` liefert JSON mit `camera_active: true`
3. Ich stelle mich vor die Kamera → nach ein paar Sekunden liefert `curl http://localhost:5000/api/events` ein neues Event mit Snapshot-Pfad, Timestamp, Confidence und Dummy-GPS-Koordinaten
4. `curl http://localhost:5000/snapshots/<dateiname>` liefert das Bild aus
5. Strg+C beendet den Prozess sauber, `/dev/video0` ist danach wieder frei (Test: `fuser /dev/video0` zeigt nichts an)

## Nicht in dieser Phase (bitte nicht vorgreifen)

- Kein Live-Stream (Phase 3)
- Kein echtes GPS-Modul (Phase 4)
- Kein Frontend/Dashboard (Phase 5)
- Kein Gunicorn/Nginx-Deployment (Phase 6)