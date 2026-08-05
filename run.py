import signal
import sys

from app import create_app

app = create_app()


def _handle_sigterm(signum, frame):
    # Werkzeugs run() faengt SystemExit nicht -- die Exception laeuft bis zum
    # try/finally unten durch, genau wie KeyboardInterrupt (SIGINT) bei Strg+C.
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        detector_thread = app.config.get("DETECTOR_THREAD")
        camera_stream = app.config.get("CAMERA_STREAM")

        if detector_thread is not None:
            detector_thread.stop()
        if camera_stream is not None:
            camera_stream.stop()
