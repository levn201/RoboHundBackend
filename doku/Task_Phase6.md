# Auftrag für Claude Code: Phase 6 (reduziert) – Autostart nach Neustart

## Kontext

Backend (Phase 2), Live-Stream (Phase 3) und Dashboard (Phase 5) sind fertig und auf dem Pi verifiziert. Aktuell muss `python run.py` immer manuell im Terminal gestartet werden. Ziel jetzt: Der Pi soll nach jedem Neustart (Stromausfall, Reboot, Update) automatisch wieder die komplette App starten, ohne dass jemand sich einloggen und `run.py` von Hand ausführen muss.

**Wichtig – Scope-Einschränkung:** In dieser Phase geht es NUR um Boot-Persistenz über systemd. Kein Nginx, kein HTTPS, keine Firewall-Konfiguration, kein externer Netzwerkzugriff – das wird später separat und eigenständig gemacht. Die App bleibt unter `http://localhost:5000` bzw. `http://<pi-ip>:5000` erreichbar wie bisher, nur eben automatisch gestartet.

## Ziel dieser Phase

1. Ein systemd-Service, der die Flask-App beim Boot automatisch startet
2. Automatischer Neustart des Service, falls die App abstürzt (z.B. Kamera-Fehler)
3. Sauberes Verhalten bei System-Shutdown (Kamera wird korrekt freigegeben, kein hängender Prozess)

## Detailanforderungen

### systemd-Service-Datei

Erstelle `deploy/watchdog.service` (im Projekt-Repo, damit sie versioniert ist) mit folgendem Inhalt/Muster:

```ini
[Unit]
Description=Watchdog Personenerkennung
After=network.target

[Service]
Type=simple
User=tnbw
WorkingDirectory=/home/tnbw/watchdog
Environment=PATH=/home/tnbw/watchdog/venv/bin
ExecStart=/home/tnbw/watchdog/venv/bin/python /home/tnbw/watchdog/run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Passe Pfade an, falls sie vom tatsächlichen Projekt-Layout abweichen (prüfe `run.py`-Pfad, venv-Pfad, User-Namen anhand der bestehenden Projektstruktur).

**Wichtige Punkte, die die Service-Datei berücksichtigen muss:**
- `After=network.target` – Kamera/Netzwerk sollten beim Start bereit sein, bevor Flask hochfährt
- `Restart=on-failure` mit `RestartSec=5` – falls die App mal abstürzt (z.B. Kamera kurzzeitig nicht erreichbar), automatischer Neuversuch nach 5 Sekunden, nicht sofort in einer Crash-Loop
- `StandardOutput=journal` / `StandardError=journal` – Logs landen in `journalctl`, nicht in einer separaten Datei (einfacher zu debuggen)
- **Kein `Type=forking`** – die App läuft im Vordergrund (`simple`), das passt zu Flasks Dev-Server

### Dokumentation der Installation

Erstelle `deploy/README.md` mit den manuellen Schritten, die ich (der Nutzer) einmalig auf dem Pi ausführen muss, um den Service zu installieren und zu aktivieren. Mindestens:

```bash
sudo cp deploy/watchdog.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable watchdog.service
sudo systemctl start watchdog.service
```

Plus Befehle zum Prüfen/Debuggen:
```bash
sudo systemctl status watchdog.service
journalctl -u watchdog.service -f
sudo systemctl restart watchdog.service
sudo systemctl stop watchdog.service
```

### Prüfen: Graceful Shutdown

Kontrolliere den bestehenden Code in `run.py` (das `finally`-Block mit `detector_thread.stop()` und `camera_stream.stop()` existiert bereits aus Phase 2) – stelle sicher, dass dieser Cleanup-Pfad auch greift, wenn systemd den Prozess per `SIGTERM` beendet (Standard-Verhalten bei `systemctl stop`), nicht nur bei Strg+C (`SIGINT`). Falls nötig, einen Signal-Handler für `SIGTERM` ergänzen, der den gleichen Cleanup auslöst.

## Akzeptanzkriterien (auf dem Pi zu testen)

1. Nach `sudo systemctl start watchdog.service`: `curl http://localhost:5000/api/status` antwortet mit `camera_active: true`
2. `sudo systemctl status watchdog.service` zeigt `active (running)`
3. **Reboot-Test:** `sudo reboot`, nach dem Hochfahren (ohne manuellen Login-Befehl, nur warten) liefert `curl http://localhost:5000/api/status` wieder eine gültige Antwort
4. **Crash-Recovery-Test:** Prozess manuell hart beenden (`sudo systemctl kill -s SIGKILL watchdog.service`), nach spätestens `RestartSec` Sekunden läuft der Service automatisch wieder (`systemctl status` zeigt neuen Start-Zeitstempel)
5. **Sauberer Stop:** `sudo systemctl stop watchdog.service`, danach `fuser /dev/video0` zeigt nichts an (Kamera sauber freigegeben, kein Zombie-Prozess)
6. Logs sind über `journalctl -u watchdog.service` einsehbar und enthalten die gewohnten Ausgaben (z.B. "Person erkannt!")

## Nicht in dieser Phase

- Kein Nginx / Reverse Proxy
- Kein HTTPS
- Keine Firewall-Regeln (UFW etc.)
- Kein Basic Auth
- Keine Snapshot-Cleanup-Cronjobs (das ist ein separater, späterer Schritt)
