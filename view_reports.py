"""
VIEW_REPORTS.py - Parking Management Report Viewer
===================================================

Used to inspect parking session history and statistics.

RUN: python view_reports.py
"""

import db
from datetime import datetime, timedelta
from typing import List, Dict

def print_table(headers: List[str], rows: List[List], max_col_widths: Dict[str, int] = None):
    """Print table in ASCII format."""
    if not rows:
        print("  (No data)")
        return
    
    if max_col_widths is None:
        max_col_widths = {h: len(h) for h in headers}
    
    for row in rows:
        for h, cell in zip(headers, row):
            max_col_widths[h] = max(max_col_widths[h], len(str(cell)))
    
    # Header
    header_line = " | ".join(h.ljust(max_col_widths[h]) for h in headers)
    print("  " + header_line)
    print("  " + "-" * len(header_line))
    
    # Rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(max_col_widths[headers[i]]) for i, cell in enumerate(row))
        print("  " + row_line)


def show_active_sessions():
    """Display currently parked vehicles."""
    print("\n" + "=" * 70)
    print("  📍 CURRENTLY PARKED VEHICLES")
    print("=" * 70)
    
    sessions = db.get_active_sessions()
    if not sessions:
        print("  (No active sessions)")
        return
    
    headers = ["Plate", "Entry Time", "Camera", "Duration (min)"]
    rows = []
    for s in sessions:
        duration_min = int((datetime.now() - datetime.fromisoformat(s['entry_time'])).total_seconds() / 60)
        rows.append([
            s['plate'],
            s['entry_time'],
            str(s.get('entry_cam', 0)),
            str(duration_min)
        ])
    
    print_table(headers, rows)


def show_recent_exits(limit: int = 20):
    """Display recent exits with billing info."""
    print("\n" + "=" * 80)
    print("  🚪 RECENT EXITS (Last {})".format(limit))
    print("=" * 80)
    
    exits = db.get_recent_exits(limit)
    if not exits:
        print("  (No exits yet)")
        return
    
    headers = ["Plate", "Entry Time", "Exit Time", "Duration (min)", "Amount (Rs)", "Status"]
    rows = []
    for e in exits:
        entry = datetime.fromisoformat(e['entry_time'])
        exit_ = datetime.fromisoformat(e['exit_time'])
        duration = int((exit_ - entry).total_seconds() / 60)
        amount = e.get('paid_amount', 0)
        status = e.get('status', 'unknown')
        
        rows.append([
            e['plate'],
            entry.strftime("%Y-%m-%d %H:%M:%S"),
            exit_.strftime("%Y-%m-%d %H:%M:%S"),
            str(duration),
            str(amount),
            status
        ])
    
    print_table(headers, rows)


def show_daily_stats():
    """Display revenue stats for today."""
    print("\n" + "=" * 70)
    print("  💰 DAILY REVENUE STATS (Today)")
    print("=" * 70)
    
    exits = db.get_recent_exits(1000)
    if not exits:
        print("  (No exits yet)")
        return
    
    # Filter for today
    today = datetime.now().date()
    today_exits = [e for e in exits if datetime.fromisoformat(e['exit_time']).date() == today]
    
    total = sum(e.get('paid_amount', 0) for e in today_exits)
    free_count = sum(1 for e in today_exits if e.get('paid_amount', 0) == 0)
    paid_count = len(today_exits) - free_count
    
    print(f"  Total Exits Today   : {len(today_exits)}")
    print(f"  Free Parking        : {free_count} vehicles (< 55 min)")
    print(f"  Paid Parking        : {paid_count} vehicles")
    print(f"  Total Revenue       : Rs {total}")
    
    if paid_count > 0:
        avg = total / paid_count
        print(f"  Average Fee (paid)  : Rs {avg:.0f}")


def show_all_time_stats():
    """Display cumulative stats."""
    print("\n" + "=" * 70)
    print("  📊 ALL-TIME STATISTICS")
    print("=" * 70)
    
    revenue = db.get_revenue()
    exits = db.get_recent_exits(10000)
    
    total_vehicles = len(exits)
    free_vehicles = sum(1 for e in exits if e.get('paid_amount', 0) == 0)
    paid_vehicles = total_vehicles - free_vehicles
    
    print(f"  Total Vehicles      : {total_vehicles}")
    print(f"  Free Parking        : {free_vehicles} ({100*free_vehicles/max(total_vehicles, 1):.1f}%)")
    print(f"  Paid Parking        : {paid_vehicles} ({100*paid_vehicles/max(total_vehicles, 1):.1f}%)")
    print(f"  Total Revenue       : Rs {revenue}")
    
    if paid_vehicles > 0:
        avg = revenue / paid_vehicles
        print(f"  Average Fee (paid)  : Rs {avg:.0f}")


def main():
    """Main menu."""
    db.init_db()
    
    while True:
        print("\n" + "=" * 70)
        print("  🅿️  PARKING MANAGEMENT REPORTS")
        print("=" * 70)
        print("  1. View Active Sessions (Currently Parked)")
        print("  2. View Recent Exits (Last 20)")
        print("  3. Daily Revenue Stats")
        print("  4. All-Time Statistics")
        print("  5. Exit")
        print("=" * 70)
        
        choice = input("  Select option (1-5): ").strip()
        
        if choice == "1":
            show_active_sessions()
        elif choice == "2":
            show_recent_exits(20)
        elif choice == "3":
            show_daily_stats()
        elif choice == "4":
            show_all_time_stats()
        elif choice == "5":
            print("\n  👋 Goodbye!\n")
            break
        else:
            print("  ❌ Invalid option")


if __name__ == "__main__":
    main()
