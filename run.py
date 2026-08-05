from app import create_app

app = create_app()

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        detector_thread = app.config.get("DETECTOR_THREAD")
        camera_stream = app.config.get("CAMERA_STREAM")

        if detector_thread is not None:
            detector_thread.stop()
        if camera_stream is not None:
            camera_stream.stop()
