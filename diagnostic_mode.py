"""
DIAGNOSTIC MODE - CONTINUOUS OCR ON EVERY FRAME
================================================

This bypasses motion detection and runs OCR on EVERY frame.
Use this to diagnose why plates aren't being captured.

RUN: python diagnostic_mode.py
"""

import cv2
import time
import os
from datetime import datetime
from typing import Tuple

from lpr import read_plate_from_frame, normalize_plate

ENTRY_CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MAX_FRAMES = 10
# If the same normalized plate appears in the last CONSENSUS_COUNT frames
# and the average confidence across those frames is >= CONSENSUS_CONF_THRESHOLD,
# the final frame will be forced to 100% (considered "fixed").
CONSENSUS_COUNT = 5
CONSENSUS_CONF_THRESHOLD = 0.90


def open_camera(cam_id: int):
    """Open camera with fallback backends."""
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    for api in backends:
        try:
            cap = cv2.VideoCapture(cam_id, api)
        except:
            cap = cv2.VideoCapture(cam_id)
        
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            return cap
    
    return None

def main():
    """Run diagnostic OCR."""
    print("\n" + "="*70)
    print("  DIAGNOSTIC MODE: Continuous OCR on every frame")
    print("="*70)
    print(f"  Camera ID: {ENTRY_CAMERA_ID}")
    print("  Press Q to stop")
    print("="*70 + "\n")
    
    cap = open_camera(ENTRY_CAMERA_ID)
    if not cap:
        print(f"  ERROR: Cannot open camera {ENTRY_CAMERA_ID}")
        return
    
    print(f"  SUCCESS: Camera opened\n")
    
    frame_count = 0
    plate_count = 0
    high_conf_count = 0
    last_plates = []  # stores tuples (norm_plate, conf)
    all_frames = []   # store frames for potential final save
    
    os.makedirs("captures", exist_ok=True)
    
    while frame_count < MAX_FRAMES:

        ret, frame = cap.read()
        if not ret:
            print("  ERROR: Frame read failed")
            break
        
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        frame_count += 1
        all_frames.append(frame.copy())
        
        # Run OCR on EVERY frame (no motion detection)
        try:
            plate, conf = read_plate_from_frame(frame)
            norm_plate = normalize_plate(plate)
            
            # Only print interesting results
            if plate:  # Non-empty result
                plate_count += 1
                if conf > 0.75:
                    high_conf_count += 1
                
                last_plates.append((norm_plate, conf))
                if len(last_plates) > MAX_FRAMES:
                    last_plates.pop(0)
                
                # Determine status label
                if conf > 0.75:
                    status = "✓ EXCELLENT"
                elif conf > 0.60:
                    status = "~ GOOD"
                elif conf > 0.45:
                    status = "! WEAK"
                else:
                    status = "X POOR"
                
                display_conf = conf
                fixed_final = False

                # Consensus check when we reach the last frame
                if frame_count == MAX_FRAMES:
                    # Look at the last CONSENSUS_COUNT detected plates (not frames)
                    recent = [p for p in last_plates if p[0]]
                    if len(recent) >= CONSENSUS_COUNT:
                        # consider the last CONSENSUS_COUNT entries
                        tail = recent[-CONSENSUS_COUNT:]
                        plates = [p for p, _ in tail]
                        confs = [c for _, c in tail]
                        # consensus if all normalized plates equal
                        if all(x == plates[0] for x in plates):
                            avg_conf = sum(confs) / len(confs)
                            if avg_conf >= CONSENSUS_CONF_THRESHOLD:
                                display_conf = 1.0
                                fixed_final = True

                print(
                    f"  Frame {frame_count:4d} | {status:12s} | Plate: {norm_plate:12s} | Conf: {display_conf:.1%}"
                )

                # Auto-save high confidence results
                if conf > 0.60:
                    filename = f"captures/diagnostic_{norm_plate}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                
                # If this is the final frame and we flagged the result as fixed,
                # save a special final capture and log it.
                if frame_count == MAX_FRAMES and fixed_final:
                    final_plate = norm_plate
                    fname = f"captures/diagnostic_fixed_{final_plate}_{int(time.time())}.jpg"
                    cv2.imwrite(fname, all_frames[-1])
                    print(f"  FINALIZED: Plate '{final_plate}' fixed and saved -> {fname}")
            
        except Exception as e:
            print(f"  Frame {frame_count:4d} | ERROR: {e}")
        
        # Display on screen
        cv2.putText(frame, f"Frame: {frame_count} | Plates found: {plate_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"High Conf (>75%): {high_conf_count}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        if last_plates:
            plate, conf = last_plates[-1]
            color = (0, 255, 0) if conf > 0.75 else (0, 165, 255) if conf > 0.50 else (0, 0, 255)
            cv2.putText(frame, f"Last: {plate} ({conf:.1%})", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.imshow("Diagnostic Mode - Continuous OCR", frame)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*70)
    print(f"  DIAGNOSTIC SUMMARY")
    print("="*70)
    print(f"  Total Frames      : {frame_count}")
    print(f"  With Any Text     : {plate_count} ({100*plate_count/max(frame_count,1):.1f}%)")
    print(f"  High Confidence   : {high_conf_count} ({100*high_conf_count/max(frame_count,1):.1f}%)")
    print("="*70)
    
    if plate_count == 0:
        print("  DIAGNOSIS: OCR is not detecting ANY text. Possible causes:")
        print("    1. Camera not pointing at license plates")
        print("    2. Image too dark or blurry")
        print("    3. EasyOCR model not loaded properly")
        print("    4. Wrong camera ID")
    elif high_conf_count == 0:
        print("  DIAGNOSIS: OCR detects text but confidence is always low (<75%)")
        print("    1. Lighting issue (too dark/bright)")
        print("    2. Image blurry or out of focus")
        print("    3. Plate image too small in frame")
        print("    4. Camera resolution issue")
    else:
        print("  DIAGNOSIS: OCR is working!")
        print("    The main system needs:")
        print("    1. Better motion detection tuning")
        print("    2. Better frame selection from buffer")
        print("    3. Check consistency check thresholds")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()