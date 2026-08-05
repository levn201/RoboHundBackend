# Projektplan: Pi-Überwachungssystem „Watchdog" 🐕

**Ziel:** Raspberry Pi 5 + USB-Kamera erkennt Personen, zeigt Snapshot, Live-Stream und GPS-Standort auf einer Website (Flask + Nginx). Später Montage auf einem Roboterhund für autonome Patrouille auf dem Firmengelände.

---

## Architektur-Überblick

```
USB-Kamera ──> Capture-Thread (OpenCV)
                    │
                    ├──> Detection-Thread (YOLOv8n / MobileNet-SSD)
                    │        ├──> Snapshot speichern (bei Person)
                    │        └──> Event in SQLite schreiben
                    │
GPS-Modul ──> gpsd ──> Position-Reader
                    │
                    └──> Flask App (API + MJPEG-Stream)
                              │
                         Gunicorn
                              │
                           Nginx ──> Browser (Dashboard)
```

**Ein Prozess, mehrere Threads.** Kamera darf nur einmal geöffnet werden – Capture-Thread liest Frames, Detection und Stream greifen auf den letzten Frame zu (Frame-Buffer mit Lock).

**Tech-Stack:**
| Komponente | Wahl | Warum |
|---|---|---|
| OS | Raspberry Pi OS Lite (64-bit) | Headless, ressourcenschonend |
| Erkennung | YOLOv8n (ultralytics) | Beste Genauigkeit/Speed-Balance auf Pi 5, ~5–10 FPS |
| Fallback-Erkennung | MobileNet-SSD (OpenCV DNN) | Schneller, falls YOLO zu langsam |
| Backend | Flask + Gunicorn | Kennst du schon |
| Webserver | Nginx (Reverse Proxy) | Kennst du schon |
| DB | SQLite | Events + Snapshots-Metadaten, kein Server nötig |
| Stream | MJPEG über Flask-Route | Einfach, kein WebRTC-Overhead |
| GPS | NEO-6M/NEO-8M über UART + gpsd | Standard, gut dokumentiert |
| Karte | Leaflet.js + OpenStreetMap | Kostenlos, kein API-Key |

---

## Phase 0 – Setup & Grundlagen (1 Abend)

- [ ] Raspberry Pi OS Lite (64-bit) auf SD flashen, SSH aktivieren
- [ ] System updaten: `sudo apt update && sudo apt full-upgrade`
- [ ] Python venv anlegen: `python3 -m venv ~/watchdog/venv`
- [ ] USB-Kamera anschließen, testen: `lsusb` und `ls /dev/video*`
- [ ] Testaufnahme: `ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg`
- [ ] Git-Repo anlegen (`watchdog`), `.gitignore` für venv/Snapshots

**Checkpoint:** Testbild von der Kamera liegt vor. ✅

---

## Phase 1 – Personenerkennung (Kern, 2–3 Abende)

- [ ] OpenCV installieren: `pip install opencv-python-headless`
- [ ] Ultralytics installieren: `pip install ultralytics`
- [ ] Script 1: Frame von Kamera lesen und als JPG speichern (OpenCV `VideoCapture`)
- [ ] Script 2: YOLOv8n auf Testbild laufen lassen, nur Klasse `person` filtern (COCO class 0)
- [ ] Script 3: Loop – Kamera lesen → Erkennung → bei Person: Snapshot mit Bounding Box + Timestamp speichern
- [ ] FPS messen. Wenn < 3 FPS: Auflösung runter (640×480) oder nur jeden n-ten Frame analysieren
- [ ] **Cooldown einbauen:** max. 1 Snapshot pro X Sekunden, sonst spammst du dir die SD-Karte voll
- [ ] Confidence-Threshold tunen (Start: 0.5)

**Checkpoint:** Du läufst durchs Bild → Snapshot mit Box um dich landet im Ordner. ✅

---

## Phase 2 – Backend: Flask App + Datenhaltung (2 Abende)

- [ ] Projektstruktur:
  ```
  watchdog/
  ├── app/
  │   ├── __init__.py      # Flask App Factory
  │   ├── camera.py        # Capture-Thread + Frame-Buffer
  │   ├── detector.py      # Detection-Thread
  │   ├── gps.py           # GPS-Reader (Phase 4, erstmal Dummy)
  │   ├── routes.py        # API + Stream
  │   └── models.py        # SQLite (Events)
  ├── snapshots/
  ├── static/ & templates/
  └── run.py
  ```
- [ ] SQLite-Tabelle `events`: `id, timestamp, confidence, snapshot_path, lat, lon`
- [ ] Capture- und Detection-Loop als Threads beim App-Start starten
- [ ] API-Routen:
  - `GET /api/events` – letzte Erkennungen (JSON)
  - `GET /api/status` – System-Status (FPS, GPS-Fix, Uptime)
  - `GET /snapshots/<file>` – Snapshot ausliefern
- [ ] GPS erstmal **mocken**: `gps.py` liefert feste Dummy-Koordinaten – Interface aber schon so bauen wie später mit echtem Modul (`get_position() -> (lat, lon)`)

**Checkpoint:** `curl localhost:5000/api/events` liefert JSON mit Erkennungen. ✅

---

## Phase 3 – Live-Stream (1 Abend)

- [ ] MJPEG-Route in Flask: Generator, der laufend den aktuellen Frame als JPEG yielded
  ```python
  @app.route('/stream')
  def stream():
      return Response(generate_frames(),
                      mimetype='multipart/x-mixed-replace; boundary=frame')
  ```
- [ ] Stream-Frame ggf. mit Bounding Boxes annotieren (nice-to-have)
- [ ] Auflösung/Qualität für Stream reduzieren (JPEG quality ~70), sonst frisst es Bandbreite

**Checkpoint:** Live-Bild im Browser unter `/stream`. ✅

---

## Phase 4 – GPS-Modul (1–2 Abende)

**Hardware:** NEO-6M oder NEO-8M Modul (~10–15 €), Anschluss über UART (GPIO 14/15) oder USB-Adapter.

- [ ] Modul verkabeln (VCC 3.3V/5V je nach Board, TX→RX, RX→TX, GND)
- [ ] UART aktivieren: `raspi-config` → Serial Port (Login-Shell aus, Hardware an)
- [ ] `gpsd` installieren: `sudo apt install gpsd gpsd-clients`
- [ ] Test: `cgps -s` → Fix bekommen (⚠️ **nur draußen / am Fenster**, drinnen kein Empfang!)
- [ ] `gps.py`: Dummy durch echten Reader ersetzen (`gpsd-py3` oder direkt NMEA parsen)
- [ ] Position bei jedem Event mit in die DB schreiben
- [ ] Fallback: kein Fix → letzte bekannte Position + Flag "GPS: no fix"

**Checkpoint:** `/api/status` zeigt echte Koordinaten. ✅

---

## Phase 5 – Frontend: Dashboard (2 Abende)

- [ ] `templates/index.html` – ein Dashboard mit:
  - [ ] Live-Stream (`<img src="/stream">` – MJPEG braucht kein JS)
  - [ ] Letzter Snapshot + Zeitpunkt der letzten Erkennung
  - [ ] Event-Liste (letzte 20, per Fetch von `/api/events`, Auto-Refresh alle 5s)
  - [ ] **Leaflet-Karte** mit Marker auf aktueller Position
- [ ] Erkennungs-"Benachrichtigung": Banner/Badge auf der Seite, wenn Event < 60s alt
- [ ] Optional: Tailwind über CDN für schnelles Styling

**Checkpoint:** Ein Browser-Tab zeigt Stream, Karte und Events. ✅

---

## Phase 6 – Deployment (1 Abend – kennst du von Smart2Lose)

- [ ] Gunicorn: **1 Worker!** (`--workers 1 --threads 4`) – mehrere Worker würden die Kamera mehrfach öffnen
- [ ] systemd-Service `watchdog.service` (After=network.target, Restart=always)
- [ ] Nginx als Reverse Proxy:
  - [ ] `proxy_buffering off;` für die Stream-Route (sonst stockt MJPEG!)
  - [ ] Snapshots direkt von Nginx ausliefern (alias auf den Ordner)
- [ ] Basic Auth in Nginx (`htpasswd`) – Überwachungsbilder gehören nicht offen ins Netz
- [ ] Aufräum-Cronjob: Snapshots älter als X Tage löschen

**Checkpoint:** Pi neustarten → alles läuft von allein wieder. ✅

---

## Phase 7 – Härtung & Betrieb (laufend)

- [ ] HTTPS (self-signed oder Let's Encrypt, falls Domain)
- [ ] Logging: Erkennungen + Fehler nach `journald`, `logrotate` prüfen
- [ ] SD-Karten-Schonung: Snapshots ggf. auf USB-Stick/NAS (→ dein Nextcloud!) auslagern
- [ ] Watchdog für den Watchdog: systemd `WatchdogSec` oder Healthcheck-Cron
- [ ] Temperatur im Auge behalten: YOLO-Dauerlast heizt den Pi 5 → aktiver Kühler empfohlen

---

## Phase 8 – Roboterhund & Firmengelände (Zukunft)

- [ ] **Stromversorgung:** Powerbank/Akku mit stabilen 5V/5A (Pi 5 ist zickig bei Unterspannung)
- [ ] **Netzwerk unterwegs:** WLAN-Abdeckung auf dem Gelände prüfen, sonst LTE-Stick + VPN (WireGuard) zurück zum Server
- [ ] Architektur-Umbau: Pi sendet Events/Streams an zentralen Server (dein Ubuntu-VM-Setup), Website läuft dort statt auf dem Pi
- [ ] Vibrations-/Wetterfestigkeit: Gehäuse, Kamera-Dämpfung
- [ ] ⚠️ **DSGVO & Recht (nicht optional!):**
  - [ ] Videoüberwachung auf Firmengelände = Verarbeitung personenbezogener Daten (Art. 6 DSGVO)
  - [ ] Datenschutzbeauftragten der Firma einbinden, Betriebsrat falls Mitarbeiter erfasst werden (§ 87 BetrVG)
  - [ ] Hinweisschilder, Löschfristen, Datenschutz-Folgenabschätzung
  - [ ] Bei KRITIS-Gelände zusätzlich mit IT-Sicherheit/Physical Security abstimmen

---

## Empfohlene Reihenfolge (TL;DR)

**Erst Pi & Erkennung, dann Website.** Grund: Die Erkennung ist das technische Risiko (Performance auf dem Pi). Wenn die läuft, ist der Rest Standard-Webentwicklung, die du eh beherrschst.

1. Phase 0 → 1: Kamera + Erkennung lokal zum Laufen bringen
2. Phase 2 → 3: Flask drumherum bauen (GPS gemockt)
3. Phase 4: GPS-Hardware nachrüsten
4. Phase 5: Dashboard
5. Phase 6 → 7: Sauber deployen & härten
6. Phase 8: Roboterhund, wenn alles stabil läuft

**Einkaufsliste:**
- [ ] GPS-Modul NEO-6M/8M mit Antenne (~10–15 €)
- [ ] Aktiver Kühler für Pi 5 (falls nicht vorhanden)
- [ ] Optional: USB-Stick für Snapshots
