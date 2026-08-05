# Auftrag für Claude Code: Phase 3 – Live-Stream

## Kontext

Phase 2 (Flask-Backend mit Camera-Thread, Detection-Thread, SQLite-Events, API-Routen) ist fertig und getestet. Jetzt kommt der Live-Stream dazu: eine MJPEG-Route, die den aktuellen Kamera-Frame kontinuierlich als Video-Stream ausliefert, direkt im Browser über ein `<img>`-Tag einbindbar (kein JavaScript/WebRTC nötig).

## Ziel dieser Phase

Eine neue Route `/stream`, die auf den bestehenden `CameraStream`-Frame-Buffer aus `app/camera.py` zugreift (NICHT die Kamera erneut öffnen!) und die Frames als `multipart/x-mixed-replace` MJPEG-Stream ausliefert.

## Detailanforderungen

### Neue Route in `app/routes.py`

- `GET /stream` – MJPEG-Stream-Route
- Nutzt einen Python-Generator, der in einer Schleife:
  1. Den aktuellsten Frame über `camera_stream.get_frame()` holt (die bestehende Methode aus `app/camera.py`, NICHT neu implementieren oder Kamera zusätzlich öffnen)
  2. Den Frame mit `cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])` zu JPEG-Bytes encodiert (Qualität 70, um Bandbreite zu sparen)
  3. Die Bytes im `multipart/x-mixed-replace`-Format yielded:
     ```python
     yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
     ```
  4. Eine kurze Pause einbaut (`time.sleep(0.1)`, ca. 10 FPS für den Stream – das ist unabhängig von `DETECTION_INTERVAL` aus der Erkennung, der Stream darf flüssiger laufen als die Erkennung)
- Response mit `mimetype='multipart/x-mixed-replace; boundary=frame'`

### Wichtige Randbedingungen

1. **Keine zweite Kamera-Instanz.** Der Stream-Generator darf ausschließlich über die bestehende `CameraStream`-Instanz aus `app/camera.py` gehen (gleiche Instanz, die auch der Detection-Thread nutzt). Prüfe, wie die Instanz aktuell in der App verfügbar gemacht wird (z.B. über die App-Factory oder ein globales Objekt) und nutze das gleiche Muster.
2. **Thread-Sicherheit:** `get_frame()` existiert bereits mit Lock-Schutz aus Phase 2 – einfach wiederverwenden, nicht verändern.
3. **Kein Blockieren des Hauptprozesses:** Der Generator läuft während der Response, muss aber sauber enden, wenn der Client die Verbindung trennt (kein Ressourcen-Leck bei Verbindungsabbruch – Flask/Werkzeug handhabt das i.d.R. automatisch bei Generator-Responses, aber kurz gegenprüfen).
4. **Fehlerbehandlung:** Falls `get_frame()` `None` zurückgibt (z.B. Kamera noch nicht bereit), den Frame in der Loop überspringen statt einen Fehler zu werfen.

### Kein Frontend in dieser Phase

Nur die Route selbst. Zum Testen reicht ein einfacher `<img src="http://<pi-ip>:5000/stream">` Tag in einer簡単en Test-HTML-Datei oder direkt der Aufruf im Browser (`http://<pi-ip>:5000/stream` öffnen zeigt bereits das Live-Bild, MJPEG wird von Browsern nativ dargestellt).

## Akzeptanzkriterien

1. `python run.py` startet weiterhin ohne Fehler (Camera- und Detection-Thread laufen wie in Phase 2)
2. Im Browser `http://<pi-ip>:5000/stream` öffnen → zeigt laufendes Live-Bild von der Kamera
3. Gleichzeitig weiterhin funktionsfähig: `/api/events`, `/api/status` – die Erkennung darf durch den Stream nicht beeinträchtigt werden (Kamera wird ja nur einmal geöffnet und geteilt)
4. Mehrere Browser-Tabs mit `/stream` gleichzeitig öffnen → alle zeigen das Bild, kein Absturz
5. Tab schließen (Verbindungsabbruch) → Server läuft stabil weiter, kein Hängenbleiben

## Nicht in dieser Phase

- Kein GPS (kommt Phase 4)
- Kein Dashboard/Frontend (kommt Phase 5)
- Keine Bounding-Boxes im Stream-Bild nötig (nice-to-have, aber nicht Pflicht – falls einfach machbar, gerne die Boxes vom letzten Detection-Result mit einzeichnen, sonst roher Kamera-Frame)
