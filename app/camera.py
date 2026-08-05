import threading
import time

import cv2

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH


class CameraStream:
    """Oeffnet die Kamera einmalig und haelt den aktuellsten Frame in einem
    thread-sicheren Buffer. Alle anderen Module lesen Frames ausschliesslich
    ueber get_frame() -- niemand ausser dieser Klasse ruft cv2.VideoCapture auf.
    """

    def __init__(self, camera_index=CAMERA_INDEX, width=FRAME_WIDTH, height=FRAME_HEIGHT):
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError("Kamera konnte nicht geoeffnet werden!")

        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _update(self):
        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            with self._lock:
                self._frame = frame

    def get_frame(self):
        """Gibt eine Kopie des aktuellsten Frames zurueck (oder None, falls noch keiner vorliegt)."""
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()

    def is_active(self):
        return self._running and self.cap.isOpened()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        self.cap.release()
