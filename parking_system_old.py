"""
COMPLETE DUAL CAMERA PARKING SYSTEM
- Entry Camera: Detects & records vehicle entry
- Exit Camera: Detects & records vehicle exit + calculates fee
- Motion Detection: Only triggers OCR when vehicle detected
- Database: Tracks all transactions
- Payment Display: Shows bill details
"""

import cv2
import time
import re
import threading
import sqlite3
from collections import deque, Counter
from datetime import datetime
import numpy as np

import db
from billing import calc_amount
from lpr import read_plate_from_frame

# Configuration
ENTRY_CAMERA_ID = 0
EXIT_CAMERA_ID = 1  # USB webcam (use camera ID 1 for exit)

PLATE_REGEX = re.compile(r"^[A-Z0-9]{6,10}$")
CONF_THRESH = 0.5  # Lowered from 0.75 for better detection
CONSISTENCY_FRAMES = 2  # Reduced from 3 for faster detection
WINDOW_SIZE = 6
COOLDOWN = 8

# Motion detection threshold
MOTION_THRESHOLD = 1000  # pixels changed

# Track recent detections
entry_recent = deque(maxlen=WINDOW_SIZE)
exit_recent = deque(maxlen=WINDOW_SIZE)

entry_last_seen = {}
exit_last_seen = {}

# System stats
parking_stats = {
    "cars_in_lot": 0,
    "total_entry": 0,
    "total_exit": 0,
    "total_revenue": 0.0
}

def detect_motion(frame1, frame2):
    """Detect motion between two frames"""
    if frame1 is None or frame2 is None:
        return False
    
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    diff = cv2.absdiff(gray1, gray2)
    motion_pixels = cv2.countNonZero(cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)[1])
    
    return motion_pixels > MOTION_THRESHOLD


def open_camera_with_backends(cam_id: int):
    """Try opening camera with several backends for better compatibility."""
    # Try DirectShow (Windows), MSMF, then default
    backends = []
    try:
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    except Exception:
        backends = [cv2.CAP_ANY]

    for api in backends:
        try:
            cap = cv2.VideoCapture(cam_id, api)
        except Exception:
            cap = cv2.VideoCapture(cam_id)

        if cap is not None and cap.isOpened():
            return cap
        else:
            try:
                cap.release()
            except Exception:
                pass

    return None

def valid_plate(p):
    return PLATE_REGEX.match(p)

def get_parking_status():
    """Get current parking lot status"""
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    
    # Count cars currently in lot
    cur.execute("SELECT COUNT(*) FROM sessions WHERE status='IN'")
    cars_in = cur.fetchone()[0]
    
    # Get total revenue
    cur.execute("SELECT SUM(paid_amount) FROM sessions WHERE paid_amount > 0")
    revenue = cur.fetchone()[0] or 0.0
    
    conn.close()
    
    parking_stats["cars_in_lot"] = cars_in
    parking_stats["total_revenue"] = revenue
    
    return cars_in, revenue

def display_payment(plate, entry_time, amount, billed_hours):
    """Display payment details on console"""
    print("\n" + "="*60)
    print("                    🧾 PARKING BILL")
    print("="*60)
    print(f"  License Plate     : {plate}")
    print(f"  Entry Time        : {entry_time}")
    print(f"  Exit Time         : {datetime.now().isoformat(timespec='seconds')}")
    print(f"  Duration          : {(datetime.fromisoformat(datetime.now().isoformat(timespec='seconds')) - datetime.fromisoformat(entry_time)).total_seconds() / 3600:.2f} hours")
    print(f"  Billable Hours    : {billed_hours}")
    
    if amount == 0:
        print(f"  Amount            : FREE PARKING (< 55 min)")
    else:
        print(f"  Amount            : Rs {amount:.2f} @ Rs 50/hour")
    
    print("="*60)
    print("  ✅ Payment Processed - Gate Opening...")
    print("="*60 + "\n")

def simulate_gate_open():
    """Simulate gate opening"""
    print("  🚪 [GATE OPENING IN PROGRESS...]")
    time.sleep(2)
    print("  ✅ Gate Fully Open - Vehicle May Exit")
    time.sleep(1)

def process_entry_camera(cam_id=ENTRY_CAMERA_ID):
    """ENTRY CAMERA: Detects vehicles entering and records entry"""
    print("\n" + "="*60)
    print("  [ENTRY CAMERA] Starting...")
    print("="*60)
    
    cap = open_camera_with_backends(cam_id)
    if cap is None:
        print(f"  ❌ FAILED: Cannot open camera {ENTRY_CAMERA_ID}")
        print("  💡 Make sure camera is connected and accessible")
        return
    
    print(f"  ✅ Camera {ENTRY_CAMERA_ID} Connected")
    
    prev_frame = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ❌ Frame read failed")
            break
        
        frame_count += 1
        display_frame = frame.copy()
        
        # Add status text
        cars_in, revenue = get_parking_status()
        status_text = f"Cars in lot: {cars_in} | Revenue: Rs {revenue:.2f}"
        cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 255, 0), 2)
        cv2.putText(display_frame, "ENTRY CAMERA", (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                   0.8, (0, 255, 0), 2)
        
        # Motion detection - only process if motion detected
        if prev_frame is not None and detect_motion(prev_frame, frame):
            plate, conf = read_plate_from_frame(frame)
            
            if plate and conf > CONF_THRESH and valid_plate(plate):
                entry_recent.append(plate)
                
                counts = Counter(entry_recent)
                if counts[plate] >= CONSISTENCY_FRAMES:
                    now = time.time()
                    if now - entry_last_seen.get(plate, 0) > COOLDOWN:
                        print(f"\n  🚗 VEHICLE DETECTED AT ENTRY")
                        print(f"     Plate: {plate} (Confidence: {conf:.2%})")
                        
                        # Save image
                        import os
                        os.makedirs("captures", exist_ok=True)
                        filename = f"captures/entry_{plate}_{int(now)}.jpg"
                        cv2.imwrite(filename, frame)
                        
                        # Record entry in database
                        ok, msg = db.start_parking(plate)
                        print(f"     {msg}")
                        
                        parking_stats["total_entry"] += 1
                        entry_last_seen[plate] = now
                        entry_recent.clear()
                        
                        print("     ✅ ENTRY RECORDED\n")
        
        prev_frame = frame.copy()
        
        # Display and key handling (press 'e' to force entry capture, 'q' to quit)
        cv2.imshow("[ENTRY CAMERA] Press Q to exit", display_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("  ⏹️ ENTRY Camera stopped")
            break
        if key == ord("e"):
            # force an OCR capture immediately
            try:
                # prepare frame (apply ROI if enabled)
                if ROI_ENABLED:
                    fh, fw = frame.shape[:2]
                    x_frac, y_frac, w_frac, h_frac = ROI_BOX
                    x = int(max(0, x_frac * fw))
                    y = int(max(0, y_frac * fh))
                    ww = int(max(10, min(fw - x, w_frac * fw)))
                    hh = int(max(10, min(fh - y, h_frac * fh)))
                    crop_frame = frame[y:y+hh, x:x+ww].copy()
                else:
                    crop_frame = frame.copy()
                # push and wait for result
                try:
                    while True:
                        frame_q.get_nowait()
                except Empty:
                    pass
                frame_q.put_nowait(crop_frame)
                plate, conf = result_q.get(timeout=OCR_GET_TIMEOUT)
            except Exception:
                plate, conf = None, 0.0

            if plate and conf > CONF_THRESH and valid_plate(plate):
                print(f"\n  [MANUAL] Entry Plate: {plate} ({conf:.2%})")
                now = time.time()
                os.makedirs("captures", exist_ok=True)
                filename = f"captures/entry_{plate}_{int(now)}.jpg"
                cv2.imwrite(filename, frame)
                ok, msg = db.start_parking(plate)
                print(f"     {msg}")
                parking_stats["total_entry"] += 1
                entry_last_seen[plate] = now
                entry_recent.clear()
    
    cap.release()
    cv2.destroyAllWindows()

def process_exit_camera(cam_id=EXIT_CAMERA_ID):
    """EXIT CAMERA: Detects vehicles exiting, calculates fee, opens gate"""
    print("\n" + "="*60)
    print("  [EXIT CAMERA] Starting...")
    print("="*60)
    
    cap = open_camera_with_backends(cam_id)
    if cap is None:
        print(f"  ❌ FAILED: Cannot open camera {EXIT_CAMERA_ID}")
        print("  💡 Try changing EXIT_CAMERA_ID, check camera connection, or run single-camera mode")
        return
    
    print(f"  ✅ Camera {EXIT_CAMERA_ID} Connected")
    
    prev_frame = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ❌ Frame read failed")
            break
        
        frame_count += 1
        display_frame = frame.copy()
        
        # Add status text
        cars_in, revenue = get_parking_status()
        status_text = f"Cars in lot: {cars_in} | Revenue: Rs {revenue:.2f}"
        cv2.putText(display_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, (0, 255, 255), 2)
        cv2.putText(display_frame, "EXIT CAMERA", (10, 70), cv2.FONT_HERSHEY_SIMPLEX,
                   0.8, (0, 255, 255), 2)
        
        # Motion detection - only process if motion detected
        if prev_frame is not None and detect_motion(prev_frame, frame):
            plate, conf = read_plate_from_frame(frame)
            
            if plate and conf > CONF_THRESH and valid_plate(plate):
                exit_recent.append(plate)
                
                counts = Counter(exit_recent)
                if counts[plate] >= CONSISTENCY_FRAMES:
                    now = time.time()
                    if now - exit_last_seen.get(plate, 0) > COOLDOWN:
                        print(f"\n  🚙 VEHICLE DETECTED AT EXIT")
                        print(f"     Plate: {plate} (Confidence: {conf:.2%})")
                        
                        # Save image
                        import os
                        os.makedirs("captures", exist_ok=True)
                        filename = f"captures/exit_{plate}_{int(now)}.jpg"
                        cv2.imwrite(filename, frame)
                        
                        # Get entry time from database
                        conn = sqlite3.connect(db.DB_NAME)
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT entry_time FROM sessions WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
                            (plate,)
                        )
                        row = cur.fetchone()
                        conn.close()
                        
                        if not row:
                            print(f"     ❌ No active entry found for {plate}")
                            print(f"     💡 This vehicle may not have entry record\n")
                        else:
                            entry_time = row[0]
                            exit_time = datetime.now().isoformat(timespec="seconds")
                            amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)
                            
                            # Display payment information
                            display_payment(plate, entry_time, amount, billed_hours)
                            
                            # Record exit in database
                            ok, msg = db.end_parking(plate, amount)
                            print(f"     {msg}")
                            
                            parking_stats["total_exit"] += 1
                            parking_stats["total_revenue"] += amount
                            
                            # Simulate gate opening
                            simulate_gate_open()
                            print()
                        
                        exit_last_seen[plate] = now
                        exit_recent.clear()
        
        prev_frame = frame.copy()
        
        # Display and key handling (press 'c' to force exit capture, 'q' to quit)
        cv2.imshow("[EXIT CAMERA] Press Q to exit", display_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("  ⏹️ EXIT Camera stopped")
            break
        if key == ord("c"):
            # force an OCR capture immediately
            try:
                if ROI_ENABLED:
                    fh, fw = frame.shape[:2]
                    x_frac, y_frac, w_frac, h_frac = ROI_BOX
                    x = int(max(0, x_frac * fw))
                    y = int(max(0, y_frac * fh))
                    ww = int(max(10, min(fw - x, w_frac * fw)))
                    hh = int(max(10, min(fh - y, h_frac * fh)))
                    crop_frame = frame[y:y+hh, x:x+ww].copy()
                else:
                    crop_frame = frame.copy()
                try:
                    while True:
                        frame_q.get_nowait()
                except Empty:
                    pass
                frame_q.put_nowait(crop_frame)
                plate, conf = result_q.get(timeout=OCR_GET_TIMEOUT)
            except Exception:
                plate, conf = None, 0.0

            if plate and conf > CONF_THRESH and valid_plate(plate):
                print(f"\n  [MANUAL] Exit Plate: {plate} ({conf:.2%})")
                now = time.time()
                os.makedirs("captures", exist_ok=True)
                filename = f"captures/exit_{plate}_{int(now)}.jpg"
                cv2.imwrite(filename, frame)

                conn = sqlite3.connect(db.DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    "SELECT entry_time FROM sessions WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
                    (plate,)
                )
                row = cur.fetchone()
                conn.close()

                if not row:
                    print(f"     ❌ No active entry found for {plate}")
                else:
                    entry_time = row[0]
                    exit_time = datetime.now().isoformat(timespec="seconds")
                    amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)
                    display_payment(plate, entry_time, amount, billed_hours)
                    ok, msg = db.end_parking(plate, amount)
                    print(f"     {msg}")
                    parking_stats["total_exit"] += 1
                    parking_stats["total_revenue"] += amount
                    simulate_gate_open()
    
    cap.release()
    cv2.destroyAllWindows()

def print_system_status():
    """Print system status periodically"""
    while True:
        time.sleep(10)
        cars_in, revenue = get_parking_status()
        print(f"\n📊 SYSTEM STATUS: {cars_in} cars in lot | Revenue: Rs {revenue:.2f}\n")


def scan_available_cameras(max_index=4, timeout=0.5):
    """Scan camera indices 0..max_index and return list of available indices."""
    found = []
    for i in range(0, max_index + 1):
        cap = open_camera_with_backends(i)
        if cap is not None:
            found.append(i)
            try:
                cap.release()
            except Exception:
                pass
        time.sleep(0.05)
    return found

def main():
    """Main entry point - Start dual camera system"""
    db.init_db()
    
    print("\n" + "="*60)
    print("  🅿️  DUAL CAMERA PARKING MANAGEMENT SYSTEM")
    print("="*60)
    print(f"  Entry Camera ID   : {ENTRY_CAMERA_ID}")
    print(f"  Exit Camera ID    : {EXIT_CAMERA_ID}")
    print(f"  Free Duration     : 55 minutes")
    print(f"  Billing Rate      : Rs 50 per hour")
    print(f"  Motion Detection  : ENABLED")
    print("="*60)
    print("\n  Press 'Q' in any camera window to stop that camera")
    print("  Press Ctrl+C to stop the entire system\n")
    
    # Create captures folder
    import os
    os.makedirs("captures", exist_ok=True)
    
    # Start status printer thread
    status_thread = threading.Thread(target=print_system_status, daemon=True)
    status_thread.start()
    
    # Start camera threads (attempt to auto-select if configured exit camera unavailable)
    entry_thread = None
    exit_thread = None

    test_exit = open_camera_with_backends(EXIT_CAMERA_ID)
    if test_exit is None:
        print("\n  ⚠️  Exit camera not available at configured ID — scanning for cameras...")
        available = scan_available_cameras(4)
        print(f"  🔍 Cameras found: {available}")
        if len(available) >= 2:
            chosen_entry, chosen_exit = available[0], available[1]
            print(f"  ✅ Auto-selected Entry={chosen_entry}, Exit={chosen_exit}")
            entry_thread = threading.Thread(target=process_entry_camera, args=(chosen_entry,), daemon=True)
            exit_thread = threading.Thread(target=process_exit_camera, args=(chosen_exit,), daemon=True)
            entry_thread.start()
            exit_thread.start()
        else:
            print("  ⚠️ Only one or zero cameras found — running single-camera (entry only) mode")
            entry_thread = threading.Thread(target=process_entry_camera, args=(ENTRY_CAMERA_ID,), daemon=True)
            entry_thread.start()
    else:
        # Close test handle and start both threads with configured IDs
        try:
            test_exit.release()
        except Exception:
            pass
        entry_thread = threading.Thread(target=process_entry_camera, args=(ENTRY_CAMERA_ID,), daemon=True)
        exit_thread = threading.Thread(target=process_exit_camera, args=(EXIT_CAMERA_ID,), daemon=True)
        entry_thread.start()
        exit_thread.start()

    try:
        # join threads that exist
        if entry_thread is not None:
            entry_thread.join()
        if exit_thread is not None:
            exit_thread.join()
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("  👋 PARKING SYSTEM SHUTTING DOWN...")
        print("="*60)
        cars_in, revenue = get_parking_status()
        print(f"  Final Status:")
        print(f"    - Total Entry   : {parking_stats['total_entry']}")
        print(f"    - Total Exit    : {parking_stats['total_exit']}")
        print(f"    - Cars in Lot   : {cars_in}")
        print(f"    - Total Revenue : Rs {revenue:.2f}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
