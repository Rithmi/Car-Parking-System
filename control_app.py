"""
Control UI for Parking System Engine

Provides a simple Flask UI to Start/Stop the `parking_system.py` engine,
show running status, stream live logs (SSE), and run `view_reports.py` on demand.

Run: python control_app.py
Visit: http://localhost:5001
"""

import os
import sys
import time
import json
import threading
import subprocess
from flask import Flask, render_template, jsonify, Response, request

APP_PORT = 5001
LOG_FILE = os.path.join(os.path.dirname(__file__), "engine.log")
ENGINE_SCRIPT = os.path.join(os.path.dirname(__file__), "parking_system.py")
REPORTS_SCRIPT = os.path.join(os.path.dirname(__file__), "view_reports.py")

app = Flask(__name__, template_folder="templates")

# Process handle (shared)
engine_proc = None
engine_lock = threading.Lock()


def start_engine():
    global engine_proc
    with engine_lock:
        if engine_proc and engine_proc.poll() is None:
            return False, "Engine already running"

        # Ensure log file directory exists
        log_dir = os.path.dirname(LOG_FILE) or os.getcwd()
        os.makedirs(log_dir, exist_ok=True)

        # Open log file in text mode with utf-8 encoding
        logf = open(LOG_FILE, "a", buffering=1, encoding="utf-8")

        # Launch as subprocess so camera/OpenCV runs isolated
        cmd = [sys.executable, ENGINE_SCRIPT]

        # Force child Python to use UTF-8 for stdout/stderr to avoid
        # UnicodeEncodeError on Windows consoles (emoji characters etc).
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, bufsize=1, universal_newlines=True, env=env)
        engine_proc = proc
        return True, f"Started (PID={proc.pid})"


def stop_engine():
    global engine_proc
    with engine_lock:
        if not engine_proc or engine_proc.poll() is not None:
            engine_proc = None
            return False, "Engine not running"

        try:
            engine_proc.terminate()
            # wait briefly
            try:
                engine_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                engine_proc.kill()
        finally:
            pid = engine_proc.pid
            engine_proc = None
        return True, f"Stopped (PID={pid})"


def engine_status():
    global engine_proc
    with engine_lock:
        if engine_proc and engine_proc.poll() is None:
            return True, engine_proc.pid
        return False, None


@app.route("/")
def index():
    running, pid = engine_status()
    return render_template("control.html", running=running, pid=pid)


@app.route("/api/start", methods=["POST"])
def api_start():
    ok, msg = start_engine()
    return jsonify({"success": ok, "message": msg})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    ok, msg = stop_engine()
    return jsonify({"success": ok, "message": msg})


@app.route("/api/status")
def api_status():
    running, pid = engine_status()
    return jsonify({"running": running, "pid": pid})


def stream_logs():
    """SSE stream that tails the engine log file."""
    # Make sure file exists
    open(LOG_FILE, "a", encoding="utf-8").close()

    def generate():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Seek to end
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    payload = {"line": line.rstrip()}
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    # heartbeat
                    yield ": ping\n\n"
                    time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/logs")
def logs():
    return stream_logs()


@app.route("/api/reports", methods=["POST"])
def api_reports():
    # Run view_reports.py and return its output
    try:
        cmd = [sys.executable, REPORTS_SCRIPT]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        out = proc.stdout or proc.stderr
        return jsonify({"success": True, "output": out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print(f"Starting Control UI on http://localhost:{APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
