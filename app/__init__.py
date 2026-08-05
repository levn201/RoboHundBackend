import time

from flask import Flask

from . import models
from .camera import CameraStream
from .detector import DetectionThread
from .routes import bp as api_bp


def create_app():
    app = Flask(__name__)

    models.init_db()

    camera_stream = CameraStream()
    camera_stream.start()

    detector_thread = DetectionThread(camera_stream)
    detector_thread.start()

    app.config["CAMERA_STREAM"] = camera_stream
    app.config["DETECTOR_THREAD"] = detector_thread
    app.config["START_TIME"] = time.time()

    app.register_blueprint(api_bp)

    return app
