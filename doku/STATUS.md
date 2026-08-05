# Watchdog-Projekt: Status

**Letztes Update:** 05.08.2026

**Repo:** https://github.com/levn201/RoboHundBackend
**Setup:** Entwicklung auf Dev-PC (VS Code + Claude Code), Testing auf Raspberry Pi 5 (`~/watchdog`, User `tnbw`, per SSH über Jumphost erreichbar – kein direkter Netzwerkzugriff von außen, curl-Tests laufen lokal auf dem Pi)

---

## Phasenstatus

| Phase | Inhalt | Status |
|---|---|---|
| 0 | Pi Setup, Kamera-Test, Git-Repo | ✅ fertig |
| 1 | Personenerkennung (YOLOv8n, zustandsbasierte Sessions) | ✅ fertig – `live_detection.py`, lokal auf Pi getestet |
| 2 | Flask-Backend (Camera-Thread, Detection-Thread, SQLite, API) | ✅ fertig & verifiziert auf dem Pi |
| 3 | Live-Stream (`/stream`-Route, MJPEG) | ✅ fertig & verifiziert auf dem Pi |
| 4 | GPS-Modul (echte Hardware statt Dummy) | ⏸️ **übersprungen** – Modul noch nicht bestellt, läuft weiter mit Dummy-Koordinaten (Stuttgart, 48.7758/9.1829) |
| 5 | Frontend/Dashboard (Stream, Snapshot, Event-Liste, Karte) | 🔧 **in Arbeit** – Task an Claude Code gegeben, Ergebnis noch nicht auf Pi verifiziert |
| 6 | Deployment (Gunicorn, systemd, Nginx) | ⏳ offen |
| 7 | Härtung (HTTPS, Logging, Cleanup) | ⏳ offen |
| 8 | Roboterhund-Integration & DSGVO/Recht | ⏳ offen, langfristig |

---

## Wichtige technische Erkenntnisse (Lessons Learned)

Diese Punkte haben in Phase 2/3 Zeit gekostet – beim Weiterarbeiten im Hinterkopf behalten:

1. **Claude Code behauptet manchmal "fertig", ohne es zu beweisen.** Bei der `/stream`-Route hieß es "fertig", war aber gar nicht implementiert. **Immer verlangen, dass Claude Code das Ergebnis selbst zeigt** (z.B. `grep` auf die neue Route, `curl`/Test-Client-Aufruf mit Statuscode), nicht nur eine Behauptung akzeptieren.

2. **`__pycache__` kann alte Code-Stände vortäuschen.** Nach Code-Änderungen, die nicht wie erwartet wirken, lohnt sich früh: `find ~/watchdog -type d -name "__pycache__" -exec rm -rf {} +`

3. **Generatoren in Flask (z.B. für Streaming-Routen) laufen lazy, außerhalb des Request-Kontexts.** `current_app` darf NICHT innerhalb eines Generators aufgerufen werden – Werte vorher in der View-Funktion holen und als Parameter/Closure übergeben. Sonst: `RuntimeError: Working outside of application context`.

4. **`send_from_directory()` wirft `werkzeug.exceptions.NotFound`, nicht `FileNotFoundError`.** Falls eigener Code das abfangen will, den richtigen Exception-Typ nutzen.

5. **Relative Pfade in `config.py` sind riskant.** `app.root_path` zeigt auf den `app/`-Unterordner, nicht auf das Projekt-Root. Deshalb `SNAPSHOT_DIR` (und ähnliche Pfade) immer absolut berechnen:
   ```python
   BASE_DIR = os.path.dirname(os.path.abspath(__file__))
   SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
   ```

6. **Flasks Dev-Server braucht `threaded=True`** in `app.run(...)`, sonst blockiert eine offene Streaming-Verbindung (z.B. `/stream`) alle anderen Requests. Ist in `run.py` bereits gesetzt.

7. **Git-Workflow:** Push vom Pi und vom Dev-PC laufen beide gegen `https://github.com/levn201/RoboHundBackend.git` (öffentliches Repo als gemeinsamer Sync-Punkt, kein direkter SSH-Zugriff zwischen den beiden Maschinen möglich). Auth über Personal Access Token (kein Passwort). `snapshots/` und `__pycache__/` sind korrekt in `.gitignore`.

8. **Testen auf dem Pi:** Da kein Browser-Zugriff von außen möglich ist (Jumphost-Netzwerk blockt), werden Routen ausschließlich per `curl` lokal auf dem Pi getestet (`curl http://localhost:5000/...`), nicht im Browser.

---

## Offene Fragen / Entscheidungen für später

- GPS-Modul (NEO-6M oder NEO-8M) muss noch bestellt werden, bevor Phase 4 nachgeholt werden kann
- Deployment-Ziel für Phase 6 (Gunicorn/Nginx) noch nicht im Detail besprochen
- Phase 8 (Roboterhund) braucht frühzeitige Abstimmung mit TransnetBW-Datenschutz/IT-Security wegen DSGVO auf Firmengelände

---

## Projektstruktur (Stand nach Phase 3)

```
watchdog/  (= RoboHundBackend)
├── app/
│   ├── __init__.py       # Flask App Factory
│   ├── camera.py          # CameraStream-Klasse, Thread-sicherer Frame-Buffer
│   ├── detector.py        # Detection-Thread, zustandsbasierte Sessions
│   ├── gps.py              # Dummy-GPS (Stuttgart-Koordinaten)
│   ├── routes.py           # API-Routen inkl. /stream
│   └── models.py           # SQLite Events
├── snapshots/               # (gitignored)
├── config.py                 # zentrale Konstanten, absolute Pfade
├── requirements.txt
├── run.py                    # Einstiegspunkt, threaded=True
├── live_detection.py         # Phase-1-Standalone-Script (Referenz)
└── Task_Phase*.md            # Aufträge für Claude Code je Phase
```

---

## Wie dieser Chat/Status weiterverwendet wird

Diese Datei kann in einem neuen Chat hochgeladen werden, um den Kontext wiederherzustellen, ohne den kompletten Verlauf neu erklären zu müssen. Enthält: Phasenstatus, Repo-Infos, technische Fallstricke, offene Punkte.
