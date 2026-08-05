# Watchdog – systemd Autostart (Phase 6)

Einmalige Installation auf dem Raspberry Pi, damit die App nach jedem Boot
automatisch startet.

## Voraussetzung

`/home/tnbw/watchdog` enthält das Projekt inkl. eines eingerichteten venv
unter `/home/tnbw/watchdog/venv` (siehe `requirements.txt`). Falls Pfad/User
bei dir abweichen, `deploy/watchdog.service` vorher entsprechend anpassen.

## Installation

```bash
sudo cp deploy/watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable watchdog.service
sudo systemctl start watchdog.service
```

`enable` sorgt für den Autostart beim Boot, `start` startet den Service sofort.

## Prüfen

```bash
curl http://localhost:5000/api/status
sudo systemctl status watchdog.service
```

`camera_active: true` und `active (running)` sollten erscheinen.

## Debuggen

```bash
journalctl -u watchdog.service -f
```

Zeigt die laufenden Logs (inkl. "Person erkannt!"-Ausgaben) live an.
Mit `journalctl -u watchdog.service -n 100` die letzten 100 Zeilen ohne Live-Tail.

## Service steuern

```bash
sudo systemctl restart watchdog.service
sudo systemctl stop watchdog.service
```

`stop` sendet `SIGTERM` – die App fährt Kamera und Detection-Thread sauber
herunter (siehe `run.py`), bevor der Prozess beendet wird.

## Reboot-Test

```bash
sudo reboot
```

Nach dem Hochfahren (ohne manuellen Login-Befehl, nur warten) sollte
`curl http://localhost:5000/api/status` wieder antworten.

## Crash-Recovery-Test

```bash
sudo systemctl kill -s SIGKILL watchdog.service
sudo systemctl status watchdog.service
```

Nach spätestens `RestartSec=5` Sekunden sollte der Service automatisch neu
gestartet sein (neuer Start-Zeitstempel in `status`).

## Deinstallation (falls nötig)

```bash
sudo systemctl stop watchdog.service
sudo systemctl disable watchdog.service
sudo rm /etc/systemd/system/watchdog.service
sudo systemctl daemon-reload
```
