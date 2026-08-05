import time

from flask import Blueprint, current_app, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from config import SNAPSHOT_DIR
from . import gps, models

bp = Blueprint("api", __name__)


@bp.route("/api/events")
def api_events():
    return jsonify(models.get_recent_events(limit=20))


@bp.route("/api/events/latest")
def api_events_latest():
    event = models.get_latest_event()
    if event is None:
        return jsonify({"error": "no events yet"}), 404
    return jsonify(event)


@bp.route("/api/status")
def api_status():
    camera_stream = current_app.config.get("CAMERA_STREAM")
    detector_thread = current_app.config.get("DETECTOR_THREAD")
    start_time = current_app.config.get("START_TIME", time.time())
    lat, lon = gps.get_position()

    return jsonify({
        "camera_active": bool(camera_stream and camera_stream.is_active()),
        "detection_running": bool(detector_thread and detector_thread.is_running()),
        "uptime_seconds": round(time.time() - start_time, 1),
        "last_gps_position": {"lat": lat, "lon": lon},
    })


@bp.route("/snapshots/<filename>")
def get_snapshot(filename):
    safe_filename = secure_filename(filename)
    if not safe_filename or safe_filename != filename:
        return jsonify({"error": "invalid filename"}), 404
    try:
        return send_from_directory(SNAPSHOT_DIR, safe_filename)
    except FileNotFoundError:
        return jsonify({"error": "snapshot not found"}), 404
