import os
import threading
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

from config import (
    CONFIDENCE_THRESHOLD,
    DETECTION_INTERVAL,
    SESSION_END_BUFFER,
    SNAPSHOT_DIR,
)
from . import gps, models


class DetectionThread(threading.Thread):
    """Zustandsbasierte Personenerkennung, 1:1 aus live_detection.py uebernommen.

    Liest Frames ueber CameraStream (statt eigenes cv2.VideoCapture), verwaltet
    dieselbe Session-Zustandsmaschine (neue Session bei "keine Person -> Person",
    Session-Ende erst nach SESSION_END_BUFFER Sekunden ohne Erkennung) und
    schreibt Events stattdessen in die SQLite-DB statt nur zu printen.
    """

    def __init__(self, camera_stream):
        super().__init__(daemon=True)
        self.camera_stream = camera_stream
        self._running = False

        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

        print("Lade YOLOv8n Modell...")
        self.model = YOLO("yolov8n.pt")

        # Zustand (uebernommen aus live_detection.py)
        self.session_active = False
        self.last_person_seen = None
        self.session_start = None
        self.current_event_id = None
        self.last_detection_time = 0

    def run(self):
        self._running = True
        print("Starte Live-Erkennung...")

        while self._running:
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            now = time.time()

            if now - self.last_detection_time < DETECTION_INTERVAL:
                time.sleep(0.05)
                continue
            self.last_detection_time = now

            results = self.model(frame, classes=[0], conf=CONFIDENCE_THRESHOLD, verbose=False)
            result = results[0]
            person_detected = len(result.boxes) > 0

            if person_detected:
                self.last_person_seen = now

                if not self.session_active:
                    self.session_active = True
                    self.session_start = now
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{timestamp_str}_start.jpg"
                    filepath = os.path.join(SNAPSHOT_DIR, filename)

                    annotated = result.plot()
                    cv2.imwrite(filepath, annotated)

                    max_conf = max(float(b.conf[0]) for b in result.boxes)
                    lat, lon = gps.get_position()

                    self.current_event_id = models.create_event(
                        timestamp=datetime.now().isoformat(),
                        confidence=max_conf,
                        snapshot_path=filename,
                        lat=lat,
                        lon=lon,
                    )

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Person erkannt! "
                          f"Confidence: {max_conf:.2f} -> {filepath}")

            else:
                if self.session_active and self.last_person_seen is not None:
                    if now - self.last_person_seen > SESSION_END_BUFFER:
                        duration = self.last_person_seen - self.session_start
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Session beendet. "
                              f"Dauer: {duration:.1f}s")

                        if self.current_event_id is not None:
                            models.update_event_duration(self.current_event_id, duration)

                        self.session_active = False
                        self.session_start = None
                        self.last_person_seen = None
                        self.current_event_id = None

    def is_running(self):
        return self._running and self.is_alive()

    def stop(self):
        self._running = False
