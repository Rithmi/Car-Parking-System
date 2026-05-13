# Dual Camera Parking LPR System

This project implements a dual-camera parking management system with motion-triggered capture, OCR-based license plate recognition, SQLite storage, tiered billing, and a Flask web dashboard.

Quick start (Windows):

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize database and run the main system (entry + exit cameras):

```powershell
python parking_system.py
```

4. Open the web dashboard in another terminal:

```powershell
python app.py
```

Control UI (Start/Stop engine + live logs)
----------------------------------------

You can run a small control UI to start/stop the engine and view live logs:

```powershell
python control_app.py
```

Visit: http://localhost:5001

Buttons:
- `Start System` — launches `parking_system.py` as a subprocess and writes logs to `engine.log`.
- `Stop System` — terminates the subprocess.
- `Open Reports` — runs `view_reports.py` and shows output.


Notes:
- See `SETUP_GUIDE.md` for configuration options (camera IDs, thresholds).
- If you only have one webcam, `parking_system.py` will detect it and run entry-only mode.
- To test OCR on images, run: `python test_ocr.py`.

Files of interest:
- `parking_system.py` - main dual-camera runtime
- `app.py` - Flask dashboard
- `db.py` - SQLite utilities
- `lpr.py` - OCR and ROI detection
- `billing.py` - billing rules
- `templates/dashboard.html` - web UI
- `SETUP_GUIDE.md` - detailed setup and tips

If you want, I can now: run quick static checks, patch any other issues, or create a Windows `start.ps1` helper. Which next?