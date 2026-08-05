from ultralytics import YOLO
import cv2
import time
import os
from datetime import datetime

# --- Konfiguration ---
CAMERA_INDEX = 0
DETECTION_INTERVAL = 0.4      # Sekunden zwischen Analysen (~2.5x/Sek)
SESSION_END_BUFFER = 5.0      # Sekunden ohne Person, bis Session als beendet gilt
CONFIDENCE_THRESHOLD = 0.5
SNAPSHOT_DIR = "snapshots"

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

print("Lade YOLOv8n Modell...")
model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


if not cap.isOpened():
    raise RuntimeError("Kamera konnte nicht geoeffnet werden!")

print("Kamera geoeffnet. Starte Live-Erkennung... (Strg+C zum Beenden)")

# --- Zustand ---
session_active = False
last_person_seen = None
session_start = None
last_detection_time = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Fehler beim Lesen des Frames, versuche erneut...")
            time.sleep(0.5)
            continue

        now = time.time()

        if now - last_detection_time < DETECTION_INTERVAL:
            continue
        last_detection_time = now

        results = model(frame, classes=[0], conf=CONFIDENCE_THRESHOLD, verbose=False)
        result = results[0]
        person_detected = len(result.boxes) > 0

        if person_detected:
            last_person_seen = now

            if not session_active:
                session_active = True
                session_start = now
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{SNAPSHOT_DIR}/{timestamp_str}_start.jpg"

                annotated = result.plot()
                cv2.imwrite(filename, annotated)

                max_conf = max(float(b.conf[0]) for b in result.boxes)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Person erkannt! "
                      f"Confidence: {max_conf:.2f} -> {filename}")

        else:
            if session_active and last_person_seen is not None:
                if now - last_person_seen > SESSION_END_BUFFER:
                    duration = last_person_seen - session_start
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Session beendet. "
                          f"Dauer: {duration:.1f}s")
                    session_active = False
                    session_start = None
                    last_person_seen = None

except KeyboardInterrupt:
    print("\nBeende...")
finally:
    cap.release()
