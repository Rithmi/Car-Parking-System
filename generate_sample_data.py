#!/usr/bin/env python3
"""
PARKING SYSTEM - SAMPLE DATA GENERATOR
========================================

Generates sample parking data for testing and demonstration.
Run: python generate_sample_data.py

This creates realistic test data with:
- Past entries and exits
- Various parking durations
- Calculated billing amounts
- Current active vehicles
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple
import random

def add_sample_data():
    """Add sample records to database"""
    
    try:
        import db
        from billing import calc_amount
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure you're in the correct directory")
        return False

    print("\n" + "="*70)
    print("📊 PARKING SYSTEM - SAMPLE DATA GENERATOR")
    print("="*70 + "\n")

    # Initialize database
    print("💾 Initializing database...")
    db.init_db()
    print("✓ Database ready\n")

    # Sample vehicles
    sample_plates = [
        'MH01AB1234',
        'QL9904',
        'GJ01AB5678',
        'TN07AB9012',
        'KA01AB3456',
        'DL10AB1111',
        'HR26AB2222',
        'UP16AB3333',
        'PB07AB4444',
        'WB01AB5555',
    ]

    print("📝 Adding sample data...\n")

    # Add historical data (past entries and exits)
    print("📅 Historical Records (Completed Parkings):")
    
    historical_vehicles = sample_plates[:6]
    for i, plate in enumerate(historical_vehicles):
        # Random entry time between 8 AM and 4 PM yesterday
        entry_hour = random.randint(8, 16)
        entry_time = (datetime.now() - timedelta(days=1, hours=random.randint(0, 8))).replace(
            hour=entry_hour,
            minute=random.randint(0, 59),
            second=0
        )
        
        # Random duration between 1 hour and 8 hours
        duration_hours = random.uniform(1, 8)
        exit_time = entry_time + timedelta(hours=duration_hours)
        
        # Calculate billing
        amount, actual_hours, billable = calc_amount(
            entry_time.isoformat(),
            exit_time.isoformat()
        )
        
        # Add to database using SQL directly (since end_parking requires existing entry)
        try:
            conn = sqlite3.connect('parking.db')
            conn.execute(
                """INSERT INTO sessions (plate, entry_time, exit_time, paid_amount, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (plate, entry_time.isoformat(), exit_time.isoformat(), amount, 'OUT')
            )
            conn.commit()
            conn.close()
            
            status = "FREE" if amount == 0 else f"₹{amount}"
            duration_str = f"{actual_hours:.1f}h"
            print(f"  ✓ {plate:12} | Entry: {entry_time.strftime('%H:%M')} | " +
                  f"Duration: {duration_str:>6} | Amount: {status:>8}")
        except Exception as e:
            print(f"  ❌ {plate}: {e}")

    print()
    print("🚗 Active Vehicles (Currently in Lot):")
    
    # Add current active vehicles
    active_vehicles = sample_plates[6:]
    for i, plate in enumerate(active_vehicles):
        # Entry time between 1 and 6 hours ago
        hours_ago = random.randint(1, 6)
        entry_time = datetime.now() - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
        
        try:
            success, msg = db.start_parking(plate, 0)
            if success:
                current_time = datetime.now()
                duration = (current_time - entry_time).total_seconds() / 3600
                
                # Update entry_time to realistic value
                conn = sqlite3.connect('parking.db')
                conn.execute(
                    "UPDATE sessions SET entry_time = ? WHERE plate = ? AND status = 'IN'",
                    (entry_time.isoformat(), plate)
                )
                conn.commit()
                conn.close()
                
                print(f"  ✓ {plate:12} | Parked since {entry_time.strftime('%H:%M')} | " +
                      f"Duration: {duration:.1f}h")
        except Exception as e:
            print(f"  ❌ {plate}: {e}")

    print()
    print("="*70)
    
    # Show summary
    try:
        import db
        conn = sqlite3.connect('parking.db')
        
        # Count stats
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'IN'")
        active_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'OUT'")
        completed_count = cur.fetchone()[0]
        
        cur.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM sessions WHERE status = 'OUT'")
        total_revenue = cur.fetchone()[0]
        
        cur.execute(
            "SELECT COALESCE(SUM(paid_amount), 0) FROM sessions WHERE status = 'OUT' AND created_at LIKE ?",
            (datetime.now().strftime('%Y-%m-%d') + '%',)
        )
        today_revenue = cur.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 DATABASE SUMMARY:")
        print(f"   Active Vehicles:     {active_count}")
        print(f"   Completed Parkings:  {completed_count}")
        print(f"   Today's Revenue:     ₹{today_revenue}")
        print(f"   Total Revenue:       ₹{total_revenue}")
        print()
        print("="*70)
        print("\n✅ Sample data generated successfully!\n")
        print("Start the system:")
        print("   python run_system.py")
        print("   or")
        print("   python app_ui.py\n")
        print("Then visit: http://localhost:5000\n")
        
    except Exception as e:
        print(f"❌ Error getting summary: {e}")

    return True

if __name__ == '__main__':
    try:
        success = add_sample_data()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
