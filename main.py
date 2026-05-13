"""
PARKING SYSTEM - BEST WORKING VERSION
Complete system with simulator + web dashboard + camera support
"""

import sqlite3
from datetime import datetime, timedelta
import db
from billing import calc_amount

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def display_payment(plate, entry_time, amount, billed_hours, actual_hours):
    print("\n" + "="*70)
    print("                    🧾 PARKING BILL".center(70))
    print("="*70)
    print(f"  License Plate     : {plate}".ljust(70))
    print(f"  Entry Time        : {entry_time}".ljust(70))
    print(f"  Exit Time         : {datetime.now().isoformat(timespec='seconds')}".ljust(70))
    print(f"  Duration          : {actual_hours:.2f} hours ({format_duration(actual_hours * 3600)})".ljust(70))
    print(f"  Billable Hours    : {billed_hours}".ljust(70))
    
    if amount == 0:
        print(f"  💚 Amount          : FREE PARKING (< 55 min)".ljust(70))
    else:
        print(f"  💰 Amount          : Rs {amount:.2f} @ Rs 50/hour".ljust(70))
    
    print("="*70)
    print("  ✅ Payment Processed - Gate Opening...".center(70))
    print("="*70 + "\n")

def simulate_gate_open():
    import time
    print("  🚪 [GATE OPENING IN PROGRESS...]")
    time.sleep(2)
    print("  ✅ Gate Fully Open - Vehicle May Exit\n")

def do_entry():
    plate = input("\n  🚗 Enter License Plate (e.g., QL9904): ").strip().upper()
    
    if not plate or len(plate) < 4:
        print("  ❌ Invalid plate")
        return False
    
    print(f"  ⏳ Recording entry for {plate}...")
    ok, msg = db.start_parking(plate)
    print(f"  {msg}\n")
    return ok

def do_exit():
    plate = input("\n  🚙 Enter License Plate (e.g., QL9904): ").strip().upper()
    
    if not plate or len(plate) < 4:
        print("  ❌ Invalid plate")
        return False
    
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT entry_time FROM sessions WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
        (plate,)
    )
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print(f"  ❌ No active entry found for {plate}\n")
        return False
    
    entry_time = row[0]
    exit_time = datetime.now().isoformat(timespec="seconds")
    amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)
    
    display_payment(plate, entry_time, amount, billed_hours, actual_hours)
    
    ok, msg = db.end_parking(plate, amount)
    print(f"  {msg}\n")
    simulate_gate_open()
    
    return ok

def view_all():
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 15")
    rows = cur.fetchall()
    conn.close()
    
    print("\n" + "="*100)
    print(f"{'ID':<5} {'PLATE':<12} {'ENTRY TIME':<20} {'EXIT TIME':<20} {'STATUS':<8} {'AMOUNT':<12}")
    print("="*100)
    
    if not rows:
        print("No records")
    else:
        for row in rows:
            session_id, plate, entry_time, exit_time, amount, status = row
            amount_str = f"Rs {amount:.2f}" if amount else "-"
            print(f"{session_id:<5} {plate:<12} {entry_time:<20} {exit_time or 'ACTIVE':<20} {status:<8} {amount_str:<12}")
    
    print("="*100 + "\n")

def get_stats():
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM sessions WHERE status='IN'")
    cars_in = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM sessions WHERE status='OUT'")
    exits = cur.fetchone()[0]
    
    cur.execute("SELECT SUM(paid_amount) FROM sessions WHERE paid_amount > 0")
    revenue = cur.fetchone()[0] or 0.0
    
    cur.execute("SELECT COUNT(*) FROM sessions WHERE paid_amount = 0 AND status='OUT'")
    free = cur.fetchone()[0]
    
    conn.close()
    
    print("\n" + "="*60)
    print("  📊 PARKING STATISTICS".center(60))
    print("="*60)
    print(f"  🚗 Cars in Lot        : {cars_in}".ljust(60))
    print(f"  🚙 Total Exits        : {exits}".ljust(60))
    print(f"  💚 Free Parking       : {free}".ljust(60))
    print(f"  💰 Total Revenue      : Rs {revenue:.2f}".ljust(60))
    print("="*60 + "\n")

def test_with_camera():
    """Simple camera test mode"""
    try:
        import cv2
        from lpr import read_plate_from_frame
        import re
        import time
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("  ❌ Cannot open camera\n")
            return
        
        print("  ✅ Camera opened")
        print("  📸 Show license plate to camera (keep it steady for 3+ seconds)")
        print("  💡 Tip: Make sure plate is clearly visible and well-lit")
        print("  Press 'Q' to stop\n")
        
        frame_count = 0
        last_detection = {}
        detection_buffer = {}
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("  ❌ Cannot read frame")
                break
            
            frame_count += 1
            display_frame = frame.copy()
            
            # Show status
            cv2.putText(display_frame, f"Frames: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Show plate to camera", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Keep it steady!", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            
            # Detect plate every 5 frames for faster detection
            if frame_count % 5 == 0:
                try:
                    plate, conf = read_plate_from_frame(frame)
                    
                    if plate and conf > 0.3:  # Lower threshold for better detection
                        # Buffer detections
                        if plate not in detection_buffer:
                            detection_buffer[plate] = 0
                        detection_buffer[plate] += 1
                        
                        # Need 3 consistent detections
                        if detection_buffer[plate] >= 3:
                            now = time.time()
                            if plate not in last_detection or (now - last_detection[plate]) > 5:
                                print(f"\n  ✅ PLATE DETECTED: {plate}")
                                print(f"     Confidence: {conf:.2%}")
                                last_detection[plate] = now
                                
                                # Record entry
                                ok, msg = db.start_parking(plate)
                                print(f"     {msg}")
                                
                                # Reset buffer
                                detection_buffer[plate] = 0
                        
                        # Show detection on screen
                        cv2.putText(display_frame, f"Detected: {plate} ({conf:.0%})", (10, display_frame.shape[0] - 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        # Reset buffer if low confidence
                        detection_buffer.clear()
                
                except Exception as e:
                    print(f"  ⚠️  Detection error: {str(e)[:50]}")
            
            cv2.imshow("🅿️ Parking System - Camera Mode (Press Q to exit)", display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n  ✅ Camera test stopped\n")
    
    except ImportError:
        print("  ❌ Camera requires: pip install opencv-python\n")

def main():
    db.init_db()
    
    while True:
        print("\n" + "="*70)
        print("  🅿️  PARKING MANAGEMENT SYSTEM - MAIN MENU".center(70))
        print("="*70)
        print("\n  🎛️  MODES:")
        print("  ┌─ 1. MANUAL MODE (Simulator - Best for testing)")
        print("  │  └─ Manually enter plates & calculate bills")
        print("  │")
        print("  ├─ 2. CAMERA MODE (Live detection)")
        print("  │  └─ Show license plate to camera for detection")
        print("  │")
        print("  ├─ 3. DATABASE (View records & stats)")
        print("  │  └─ See all parking sessions & revenue")
        print("  │")
        print("  ├─ 4. WEB DASHBOARD (Open browser)")
        print("  │  └─ Run: python app.py → http://localhost:5000")
        print("  │")
        print("  └─ 5. EXIT")
        print("\n" + "="*70)
        
        choice = input("\n  Choose option (1-5): ").strip()
        
        if choice == "1":
            print("\n" + "="*70)
            print("  📋 MANUAL MODE (SIMULATOR)".center(70))
            print("="*70)
            
            while True:
                print("\n  1. Record Entry")
                print("  2. Record Exit")
                print("  3. Back to main menu")
                
                sub = input("\n  Choose: ").strip()
                
                if sub == "1":
                    do_entry()
                elif sub == "2":
                    do_exit()
                elif sub == "3":
                    break
                else:
                    print("  ❌ Invalid option")
        
        elif choice == "2":
            print("\n" + "="*70)
            print("  📹 CAMERA MODE".center(70))
            print("="*70)
            test_with_camera()
        
        elif choice == "3":
            print("\n" + "="*70)
            print("  📊 DATABASE & STATISTICS".center(70))
            print("="*70)
            
            while True:
                print("\n  1. View All Records")
                print("  2. View Statistics")
                print("  3. Back to main menu")
                
                sub = input("\n  Choose: ").strip()
                
                if sub == "1":
                    view_all()
                elif sub == "2":
                    get_stats()
                elif sub == "3":
                    break
                else:
                    print("  ❌ Invalid option")
        
        elif choice == "4":
            print("\n" + "="*70)
            print("  🌐 WEB DASHBOARD".center(70))
            print("="*70)
            print("\n  To start web dashboard, run in another terminal:")
            print("  $ python app.py")
            print("\n  Then visit: http://localhost:5000\n")
        
        elif choice == "5":
            print("\n  👋 Thank you for using Parking System!\n")
            break
        
        else:
            print("\n  ❌ Invalid option\n")

if __name__ == "__main__":
    main()