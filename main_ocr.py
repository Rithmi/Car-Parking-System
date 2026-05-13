import sqlite3
from datetime import datetime

import db
from billing import calc_amount
from lpr import read_plate_from_image

ENTRY_IMAGE = ""
EXIT_IMAGE  = ""  

def get_active_entry_time(plate: str):
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT entry_time FROM sessions WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
        (plate,)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def do_entry():
    plate, conf = read_plate_from_image(ENTRY_IMAGE)
    print(f"\nOCR Plate: {plate} (conf={conf:.3f})")
    if not plate:
        print("❌ OCR failed.")
        return
    ok, msg = db.start_parking(plate)
    print(msg)

def do_exit():
    plate, conf = read_plate_from_image(EXIT_IMAGE)
    print(f"\nOCR Plate: {plate} (conf={conf:.3f})")
    if not plate:
        print("❌ OCR failed.")
        return

    entry_time = get_active_entry_time(plate)
    if not entry_time:
        print("❌ No active entry found for this plate")
        return

    exit_time = datetime.now().isoformat(timespec="seconds")
    amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)

    print("\n--- BILL DETAILS ---")
    print(f"Entry Time : {entry_time}")
    print(f"Exit Time  : {exit_time}")
    print(f"Actual hrs : {actual_hours:.2f}")
    print(f"Billed hrs : {billed_hours}")
    print(f"Amount     : Rs {amount:.2f}")

    ok, msg = db.end_parking(plate, amount)
    print(msg)

def main():
    db.init_db()
    print("=== CAR PARKING SYSTEM (OCR - IMAGE MODE) ===")

    while True:
        print("\nMenu: 1=ENTRY  2=EXIT  3=QUIT")
        choice = input("Choose: ").strip()

        if choice == "1":
            do_entry()
        elif choice == "2":
            do_exit()
        elif choice == "3":
            print("Bye!")
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()