# Auftrag für Claude Code: Phase 5 – Frontend Dashboard

## Kontext

Backend ist fertig und verifiziert: Flask-App mit Live-Stream (`/stream`), Events-API (`/api/events`, `/api/events/latest`), Status-API (`/api/status`), Snapshot-Auslieferung (`/snapshots/<filename>`). GPS liefert aktuell Dummy-Koordinaten (Stuttgart), da das echte Modul noch nicht verbaut ist – das Dashboard soll trotzdem schon eine Karte anzeigen, die später nahtlos mit echten Koordinaten funktioniert.

## Ziel dieser Phase

Eine einzelne HTML-Dashboard-Seite unter der Route `/` (Startseite), die zeigt:
1. Live-Stream
2. Letzter Snapshot mit Zeitpunkt der letzten Erkennung
3. Liste der letzten Events (auto-aktualisierend)
4. Karte mit Marker auf der aktuellen (Dummy-)Position

## Detailanforderungen

### Neue Route in `app/routes.py`

- `GET /` – rendert `templates/index.html` (Flask `render_template`)

### `app/templates/index.html`

Eine Seite mit folgenden Bereichen:

**1. Live-Stream-Bereich**
```html
<img src="/stream" alt="Live-Stream">
```
Kein JavaScript nötig, MJPEG rendert nativ im Browser.

**2. Letzter Snapshot + Zeitpunkt**
- Fetch von `/api/events/latest` beim Laden der Seite
- Zeigt Snapshot-Bild (`/snapshots/<snapshot_path>`) und formatierten Zeitpunkt
- Falls noch kein Event existiert (404 von der API): Platzhaltertext "Noch keine Erkennung"

**3. Event-Liste**
- Fetch von `/api/events` (liefert die letzten 20)
- Tabellarische oder Listen-Darstellung: Zeitpunkt, Confidence, Link/Thumbnail zum Snapshot
- **Auto-Refresh alle 5 Sekunden** (JavaScript `setInterval`, erneuter Fetch, DOM aktualisieren)

**4. Karte**
- Leaflet.js einbinden über CDN (kein API-Key nötig, OpenStreetMap-Tiles)
- Marker an Position aus `/api/status` (`last_gps_position.lat` / `.lon`)
- Karte muss beim Auto-Refresh (alle 5s, gekoppelt an den gleichen Intervall wie die Event-Liste) den Marker aktualisieren, falls sich die Position ändert (aktuell mit Dummy-Daten macht das noch keinen Unterschied, aber die Logik soll schon vorbereitet sein für Phase 4 mit echtem GPS)

**5. Erkennungs-Banner (nice-to-have, aber gewünscht)**
- Falls das letzte Event jünger als 60 Sekunden ist: auffälliges Banner/Badge oben auf der Seite ("Person erkannt vor X Sekunden")
- Verschwindet automatisch, sobald das letzte Event älter als 60s ist (wird beim Auto-Refresh neu berechnet)

### Styling

- Einfaches, aufgeräumtes Layout reicht – **Tailwind CSS über CDN** nutzen (`<script src="https://cdn.tailwindcss.com"></script>`), kein Build-Step nötig
- Responsive: sollte auch auf einem Handy-Bildschirm nutzbar sein (Grid/Flex, das auf schmalen Screens umbricht)
- Dunkles oder helles Theme ist Geschmackssache, bitte eine sinnvolle Wahl treffen und konsistent anwenden

### Wichtige Randbedingungen

1. **Kein Build-Tool, kein npm.** Alles über CDN-Links (Tailwind, Leaflet). Die Seite muss als einzelne `index.html`-Datei funktionieren, die Flask direkt rendert.
2. **JavaScript vanilla**, kein React o.ä. – hält es einfach und passt zum Rest des Projekts.
3. **Fetch-Fehler abfangen:** Falls `/api/events` oder `/api/status` mal nicht antworten (z.B. kurz nach Server-Neustart), darf die Seite nicht komplett brechen – sinnvolle Fallback-Anzeige statt kaputtem JavaScript.
4. **Flask braucht einen `templates`-Ordner** im `app`-Package (`app/templates/index.html`) – prüfen, ob die App-Factory in `__init__.py` den Template-Ordner korrekt findet (Flask sucht standardmäßig relativ zum Package, sollte automatisch funktionieren, aber gegenprüfen).

## Akzeptanzkriterien

1. `python run.py` startet weiterhin ohne Fehler
2. Im Browser `http://<pi-ip>:5000/` öffnen → zeigt Dashboard mit allen vier Bereichen
3. Live-Stream läuft im Dashboard sichtbar
4. Nach einer neuen Personenerkennung (vor die Kamera stellen): Event-Liste aktualisiert sich innerhalb von 5 Sekunden automatisch, ohne Seiten-Reload
5. Karte zeigt einen Marker an der (Dummy-)Position
6. Banner erscheint bei frischer Erkennung und verschwindet nach 60s wieder
7. Seite bricht nicht, falls z.B. `/api/events/latest` initial ein 404 liefert (noch kein Event vorhanden)

## Nicht in dieser Phase

- Kein echtes GPS (bleibt Dummy, kommt in Phase 4 nachträglich – das Dashboard muss aber schon so gebaut sein, dass ein Wechsel auf echte Koordinaten ohne Frontend-Änderung funktioniert)
- Kein Deployment/Gunicorn/Nginx (Phase 6)
- Keine Benutzer-Authentifizierung (kommt implizit über Nginx Basic Auth in Phase 6)
