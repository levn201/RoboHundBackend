CAMERA_INDEX = 0
DETECTION_INTERVAL = 0.4      # Sekunden zwischen Analysen (~2.5x/Sek)
SESSION_END_BUFFER = 5.0      # Sekunden ohne Person, bis Session als beendet gilt
CONFIDENCE_THRESHOLD = 0.5

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
DATABASE_PATH = "watchdog.db"

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Dummy-GPS-Position (Stuttgart), bis app/gps.py durch eine echte
# gpsd-Anbindung ersetzt wird (Phase 4)
DUMMY_LAT = 48.7758
DUMMY_LON = 9.1829
