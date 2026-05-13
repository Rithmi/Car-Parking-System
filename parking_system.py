"""
DUAL CAMERA PARKING MANAGEMENT SYSTEM - PRODUCTION READY WITH DEBUG MODE
=========================================================================

Features:
- 2 cameras (Entry + Exit) with motion detection
- Best-frame selection (Laplacian variance + brightness scoring)
- Plate detection (contour-based + optional YOLOv8)
- OCR with plate text normalization
- Consistency checking (2 reads required - LOWERED for testing)
- Cooldown enforcement (5 seconds between duplicate captures)
- SQLite session tracking
- Tiered billing (0-55 min free, then Rs50/hour)

RUN: python parking_system.py

USAGE:
- Entry camera: Press 'E' to force entry capture (debug manual test)
- Exit camera: Press 'C' to force exit capture (debug manual test)  
- Any camera: Press 'Q' to stop that camera
- Console: Ctrl+C to shutdown system

DEBUG MODE (enabled by default):
- Shows motion detection events
- Shows frame buffer filling progress
- Shows all OCR results (even failed ones)
- Shows consistency check progress
- Shows why plates are rejected

OPTIONAL (for AI plate detection):
pip install ultralytics
"""

import cv2
import time
import threading
import os
import numpy as np
from collections import deque, Counter
from datetime import datetime
from typing import Optional, Tuple, List

import db
from billing import calc_amount
from lpr import (
    read_plate_from_frame, detect_motion, score_frame_quality,
    select_best_frame, normalize_plate
)

# ============== TUNED CONFIGURATION ==============
ENTRY_CAMERA_ID = 0
EXIT_CAMERA_ID = 1

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
BEST_FRAME_BUFFER = 10  # Optimized: 10 frames (was 15) - faster capture

# LOWERED THRESHOLDS FOR ACTIVATION/TESTING
MOTION_THRESHOLD = 500      # Lower = more sensitive to motion
CONF_THRESH = 0.50          # Lower = accepts lower OCR confidence
CONSISTENCY_FRAMES = 2      # Need only 2 matching reads (was 3)
COOLDOWN = 5                # Faster duplicate prevention (was 8)
OCR_COOLDOWN = 2.0          # Faster OCR runs (was 4.0)

# Optional ROI cropping
ROI_ENABLED = False
ROI_BOX = (0.25, 0.5, 0.5, 0.25)

# DEBUG FLAGS - Set to True to see detailed output
DEBUG_MOTION = True
DEBUG_BUFFER = True
DEBUG_PLATE = True

# System stats
parking_stats = {"cars_in_lot": 0, "total_entry": 0, "total_exit": 0, "total_revenue": 0}
entry_recent = deque(maxlen=6)
exit_recent = deque(maxlen=6)
entry_last_seen = {}
exit_last_seen = {}


# ============== UTILITY FUNCTIONS ==============

def open_camera_with_backends(cam_id: int) -> Optional[cv2.VideoCapture]:
    """Try opening camera with multiple OpenCV backends."""
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
            try:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            except Exception:
                pass
            return cap
        else:
            try:
                cap.release()
            except Exception:
                pass
    
    return None


def get_parking_status() -> Tuple[int, int]:
    """Get current parking status."""
    active = db.get_active_sessions()
    revenue = db.get_revenue()
    parking_stats["cars_in_lot"] = len(active)
    parking_stats["total_revenue"] = revenue
    return len(active), revenue


def display_payment(plate: str, entry_time: str, amount: int, billed_hours: int):
    """Display payment bill."""
    print("\n" + "="*60)
    print("                    PARKING BILL")
    print("="*60)
    print(f"  License Plate     : {plate}")
    print(f"  Entry Time        : {entry_time}")
    print(f"  Exit Time         : {datetime.now().isoformat(timespec='seconds')}")
    print(f"  Billable Hours    : {billed_hours}")
    
    if amount == 0:
        print(f"  Amount            : FREE (< 55 min)")
    else:
        print(f"  Amount            : Rs {amount}")
    
    print("="*60)
    print("  Payment Processed - Gate Opening...")
    print("="*60 + "\n")


def simulate_gate_open():
    """Simulate gate opening."""
    print("  [GATE OPENING...]")
    time.sleep(2)
    print("  Gate Fully Open")


def process_best_frame_entry(best_frame: np.ndarray, cam_id: int) -> Tuple[str, float]:
    """Process entry frame and run OCR."""
    try:
        if ROI_ENABLED:
            fh, fw = best_frame.shape[:2]
            x_frac, y_frac, w_frac, h_frac = ROI_BOX
            x = int(max(0, x_frac * fw))
            y = int(max(0, y_frac * fh))
            ww = int(max(10, min(fw - x, w_frac * fw)))
            hh = int(max(10, min(fh - y, h_frac * fh)))
            crop = best_frame[y:y+hh, x:x+ww].copy()
        else:
            crop = best_frame.copy()
        
        plate, conf = read_plate_from_frame(crop)
        norm_plate = normalize_plate(plate)
        
        if DEBUG_PLATE:
            print(f"     [OCR] Raw: '{plate}' | Norm: '{norm_plate}' | Conf: {conf:.1%}")
        
        return norm_plate, conf
    except Exception as e:
        if DEBUG_PLATE:
            print(f"     [OCR] Error: {e}")
        return "", 0.0


def process_entry_camera(cam_id: int = ENTRY_CAMERA_ID):
    """ENTRY CAMERA: motion trigger -> best-frame selection -> OCR -> DB entry."""
    print("\n" + "="*60)
    print(f"  [ENTRY CAMERA {cam_id}] Starting...")
    print("="*60)
    
    cap = open_camera_with_backends(cam_id)
    if cap is None:
        print(f"  ERROR: Cannot open camera {cam_id}")
        return
    
    print(f"  SUCCESS: Camera {cam_id} Connected")
    
    prev_frame = None
    frame_buffer = deque(maxlen=BEST_FRAME_BUFFER)
    last_ocr_time = 0
    motion_detected = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ERROR: Frame read failed")
            break
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Motion detection
        if prev_frame is not None and detect_motion(prev_frame, frame, MOTION_THRESHOLD):
            motion_detected = True
            frame_buffer.append(frame.copy())
            if DEBUG_MOTION:
                print(f"  [ENTRY] Motion! Buffer: {len(frame_buffer)}/{BEST_FRAME_BUFFER}")
        
        # Buffer full - process best frame
        elif motion_detected and len(frame_buffer) >= BEST_FRAME_BUFFER:
            if DEBUG_BUFFER:
                print(f"  [ENTRY] Buffer FULL. Selecting best frame...")
            
            best_frame, best_idx = select_best_frame(list(frame_buffer))
            if DEBUG_BUFFER:
                print(f"  [ENTRY] Best frame selected (index {best_idx})")
            
            now = time.time()
            if now - last_ocr_time > OCR_COOLDOWN:
                plate, conf = process_best_frame_entry(best_frame, cam_id)
                
                if plate and conf > CONF_THRESH:
                    entry_recent.append(plate)
                    counts = Counter(entry_recent)
                    
                    if counts[plate] >= CONSISTENCY_FRAMES:
                        if DEBUG_PLATE:
                            print(f"  [ENTRY] CONSISTENCY PASSED ({counts[plate]}/{CONSISTENCY_FRAMES})")
                        
                        if now - entry_last_seen.get(plate, 0) > COOLDOWN:
                            print(f"\n  CAR ENTRY: {plate} ({conf:.1%})")
                            
                            os.makedirs("captures", exist_ok=True)
                            filename = f"captures/entry_{plate}_{int(now)}.jpg"
                            cv2.imwrite(filename, best_frame)
                            
                            ok, msg = db.start_parking(plate, entry_cam=cam_id)
                            print(f"     {msg}")
                            
                            parking_stats["total_entry"] += 1
                            entry_last_seen[plate] = now
                            entry_recent.clear()
                        else:
                            remaining = COOLDOWN - (now - entry_last_seen.get(plate, 0))
                            if DEBUG_PLATE:
                                print(f"  [ENTRY] COOLDOWN ({remaining:.1f}s left)")
                    else:
                        if DEBUG_PLATE:
                            print(f"  [ENTRY] CONSISTENCY IN PROGRESS ({counts[plate]}/{CONSISTENCY_FRAMES})")
                elif DEBUG_PLATE:
                    print(f"  [ENTRY] REJECTED: conf={conf:.1%} (need {CONF_THRESH}), text='{plate}'")
                
                last_ocr_time = now
            
            motion_detected = False
            frame_buffer.clear()
        
        prev_frame = frame.copy()
        
        cars_in, revenue = get_parking_status()
        cv2.putText(frame, f"Cars: {cars_in} | Revenue: Rs{revenue}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, "ENTRY CAM - Press E for manual test, Q to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow(f"[ENTRY] Camera {cam_id}", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord("q"):
            print("  ENTRY Camera stopped")
            break
        elif key == ord("e"):
            print("  [MANUAL] Processing current frame (E pressed)...")
            plate, conf = process_best_frame_entry(frame, cam_id)
            if plate:
                print(f"  MANUAL RESULT: {plate} ({conf:.1%})")
                os.makedirs("captures", exist_ok=True)
                filename = f"captures/manual_entry_{plate}_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
            else:
                print(f"  MANUAL FAILED: no plate (conf={conf:.1%})")
    
    cap.release()
    cv2.destroyAllWindows()


def process_exit_camera(cam_id: int = EXIT_CAMERA_ID):
    """EXIT CAMERA: motion trigger -> best-frame selection -> OCR -> billing -> DB exit."""
    print("\n" + "="*60)
    print(f"  [EXIT CAMERA {cam_id}] Starting...")
    print("="*60)
    
    cap = open_camera_with_backends(cam_id)
    if cap is None:
        print(f"  ERROR: Cannot open camera {cam_id}")
        return
    
    print(f"  SUCCESS: Camera {cam_id} Connected")
    
    prev_frame = None
    frame_buffer = deque(maxlen=BEST_FRAME_BUFFER)
    last_ocr_time = 0
    motion_detected = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ERROR: Frame read failed")
            break
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # Motion detection
        if prev_frame is not None and detect_motion(prev_frame, frame, MOTION_THRESHOLD):
            motion_detected = True
            frame_buffer.append(frame.copy())
            if DEBUG_MOTION:
                print(f"  [EXIT] Motion! Buffer: {len(frame_buffer)}/{BEST_FRAME_BUFFER}")
        
        # Buffer full - process best frame
        elif motion_detected and len(frame_buffer) >= BEST_FRAME_BUFFER:
            if DEBUG_BUFFER:
                print(f"  [EXIT] Buffer FULL. Selecting best frame...")
            
            best_frame, best_idx = select_best_frame(list(frame_buffer))
            if DEBUG_BUFFER:
                print(f"  [EXIT] Best frame selected (index {best_idx})")
            
            now = time.time()
            if now - last_ocr_time > OCR_COOLDOWN:
                plate, conf = process_best_frame_entry(best_frame, cam_id)
                
                if plate and conf > CONF_THRESH:
                    exit_recent.append(plate)
                    counts = Counter(exit_recent)
                    
                    if counts[plate] >= CONSISTENCY_FRAMES:
                        if DEBUG_PLATE:
                            print(f"  [EXIT] CONSISTENCY PASSED ({counts[plate]}/{CONSISTENCY_FRAMES})")
                        
                        if now - exit_last_seen.get(plate, 0) > COOLDOWN:
                            print(f"\n  CAR EXIT: {plate} ({conf:.1%})")
                            
                            os.makedirs("captures", exist_ok=True)
                            filename = f"captures/exit_{plate}_{int(now)}.jpg"
                            cv2.imwrite(filename, best_frame)
                            
                            # Lookup entry in DB
                            sessions = db.get_active_sessions()
                            entry_time = None
                            for sess in sessions:
                                if normalize_plate(sess['plate']) == plate:
                                    entry_time = sess['entry_time']
                                    break
                            
                            if not entry_time:
                                print(f"     [ERROR] No entry found for {plate}")
                            else:
                                exit_time = datetime.now().isoformat(timespec="seconds")
                                amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)
                                
                                display_payment(plate, entry_time, amount, billed_hours)
                                ok, msg = db.end_parking(plate, amount, exit_cam=cam_id)
                                print(f"     {msg}")
                                
                                parking_stats["total_exit"] += 1
                                parking_stats["total_revenue"] += amount
                                
                                simulate_gate_open()
                            
                            exit_last_seen[plate] = now
                            exit_recent.clear()
                        else:
                            remaining = COOLDOWN - (now - exit_last_seen.get(plate, 0))
                            if DEBUG_PLATE:
                                print(f"  [EXIT] COOLDOWN ({remaining:.1f}s left)")
                    else:
                        if DEBUG_PLATE:
                            print(f"  [EXIT] CONSISTENCY IN PROGRESS ({counts[plate]}/{CONSISTENCY_FRAMES})")
                elif DEBUG_PLATE:
                    print(f"  [EXIT] REJECTED: conf={conf:.1%} (need {CONF_THRESH}), text='{plate}'")
                
                last_ocr_time = now
            
            motion_detected = False
            frame_buffer.clear()
        
        prev_frame = frame.copy()
        
        cars_in, revenue = get_parking_status()
        cv2.putText(frame, f"Cars: {cars_in} | Revenue: Rs{revenue}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, "EXIT CAM - Press C for manual test, Q to quit", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        cv2.imshow(f"[EXIT] Camera {cam_id}", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord("q"):
            print("  EXIT Camera stopped")
            break
        elif key == ord("c"):
            print("  [MANUAL] Processing current frame (C pressed)...")
            plate, conf = process_best_frame_entry(frame, cam_id)
            if plate:
                print(f"  MANUAL RESULT: {plate} ({conf:.1%})")
                os.makedirs("captures", exist_ok=True)
                filename = f"captures/manual_exit_{plate}_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
            else:
                print(f"  MANUAL FAILED: no plate (conf={conf:.1%})")
    
    cap.release()
    cv2.destroyAllWindows()


def scan_available_cameras(max_index: int = 4) -> List[int]:
    """Scan and return list of available camera indices."""
    found = []
    for i in range(0, max_index + 1):
        cap = open_camera_with_backends(i)
        if cap is not None:
            found.append(i)
            try:
                cap.release()
            except:
                pass
        time.sleep(0.05)
    return found


def main():
    """Main entry point."""
    db.init_db()
    
    print("\n" + "="*60)
    print("  DUAL CAMERA PARKING SYSTEM (DEBUG MODE ON)")
    print("="*60)
    print(f"  Entry Camera     : {ENTRY_CAMERA_ID}")
    print(f"  Exit Camera      : {EXIT_CAMERA_ID}")
    print(f"  Motion Threshold : {MOTION_THRESHOLD}")
    print(f"  OCR Confidence   : {CONF_THRESH}")
    print(f"  Consistency Need : {CONSISTENCY_FRAMES}")
    print("="*60 + "\n")
    
    os.makedirs("captures", exist_ok=True)
    
    # Check cameras
    test_entry = open_camera_with_backends(ENTRY_CAMERA_ID)
    test_exit = open_camera_with_backends(EXIT_CAMERA_ID)
    
    entry_cam_id = ENTRY_CAMERA_ID
    exit_cam_id = EXIT_CAMERA_ID
    
    if test_entry is None or test_exit is None:
        print("  WARNING: One or both cameras unavailable. Scanning...")
        available = scan_available_cameras()
        print(f"  Found cameras: {available}")
        if len(available) >= 2:
            entry_cam_id, exit_cam_id = available[0], available[1]
            print(f"  Auto-selected: Entry={entry_cam_id}, Exit={exit_cam_id}")
        elif len(available) == 1:
            print("  Only one camera found. Running entry-only mode.")
            entry_cam_id = available[0]
            exit_cam_id = -1
    
    # Close test handles
    try:
        if test_entry: test_entry.release()
        if test_exit: test_exit.release()
    except:
        pass
    
    # Start camera threads
    entry_thread = threading.Thread(target=process_entry_camera, args=(entry_cam_id,), daemon=True)
    exit_thread = None
    
    if exit_cam_id >= 0:
        exit_thread = threading.Thread(target=process_exit_camera, args=(exit_cam_id,), daemon=True)
        exit_thread.start()
    
    entry_thread.start()
    
    try:
        entry_thread.join()
        if exit_thread:
            exit_thread.join()
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("  SYSTEM SHUTTING DOWN...")
        print("="*60)
        cars_in, revenue = get_parking_status()
        print(f"  Total Entries   : {parking_stats['total_entry']}")
        print(f"  Total Exits     : {parking_stats['total_exit']}")
        print(f"  Cars in Lot     : {cars_in}")
        print(f"  Total Revenue   : Rs {revenue}")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
