#!/usr/bin/env python3
"""
PARKING SYSTEM - TEST SCRIPT
=============================

This script tests all components of the parking management system.
Run: python test_system.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

def print_header():
    print("\n" + "="*70)
    print("🧪 PARKING SYSTEM - COMPONENT TEST")
    print("="*70 + "\n")

def test_imports():
    """Test all imports"""
    print("📦 Testing Imports...")
    
    try:
        import db
        print("  ✓ db module")
    except Exception as e:
        print(f"  ❌ db module: {e}")
        return False
    
    try:
        import billing
        print("  ✓ billing module")
    except Exception as e:
        print(f"  ❌ billing module: {e}")
        return False
    
    try:
        import flask
        print("  ✓ Flask")
    except Exception as e:
        print(f"  ❌ Flask: {e}")
        print("     Run: pip install flask")
        return False
    
    try:
        from flask_cors import CORS
        print("  ✓ Flask-CORS")
    except Exception as e:
        print(f"  ❌ Flask-CORS: {e}")
        print("     Run: pip install flask-cors")
        return False
    
    try:
        import cv2
        print("  ✓ OpenCV")
    except Exception as e:
        print(f"  ⚠️  OpenCV: {e} (optional)")
    
    print()
    return True

def test_database():
    """Test database operations"""
    print("💾 Testing Database...")
    
    try:
        import db
        
        # Initialize
        db.init_db()
        print("  ✓ Database initialized")
        
        # Test entry
        success, msg = db.start_parking('TEST0001', 0)
        print(f"  ✓ Record entry: {msg}")
        
        # Test exit
        from billing import calc_amount
        entry_time = (datetime.now() - timedelta(hours=2)).isoformat()
        exit_time = datetime.now().isoformat()
        amount, _, _ = calc_amount(entry_time, exit_time)
        
        success, msg = db.end_parking('TEST0001', amount, 1)
        print(f"  ✓ Record exit: {msg}")
        
        # Test query
        active = db.get_active_sessions()
        print(f"  ✓ Active vehicles: {len(active)} found")
        
        recent = db.get_recent_exits(5)
        print(f"  ✓ Recent exits: {len(recent)} found")
        
        revenue = db.get_revenue()
        print(f"  ✓ Total revenue: ₹{revenue}")
        
        print()
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        print()
        return False

def test_billing():
    """Test billing calculations"""
    print("💰 Testing Billing System...")
    
    try:
        from billing import calc_amount
        
        # Test 1: Free parking (30 minutes)
        entry = datetime.now() - timedelta(minutes=30)
        exit_t = datetime.now()
        amount, hours, billable = calc_amount(entry.isoformat(), exit_t.isoformat())
        assert amount == 0, f"Expected free, got ₹{amount}"
        print("  ✓ 30 min = FREE")
        
        # Test 2: 1 hour
        entry = datetime.now() - timedelta(hours=1, minutes=30)
        exit_t = datetime.now()
        amount, hours, billable = calc_amount(entry.isoformat(), exit_t.isoformat())
        assert amount == 50, f"Expected ₹50, got ₹{amount}"
        print("  ✓ 90 min = ₹50")
        
        # Test 3: 2 hours
        entry = datetime.now() - timedelta(hours=2)
        exit_t = datetime.now()
        amount, hours, billable = calc_amount(entry.isoformat(), exit_t.isoformat())
        assert amount == 100, f"Expected ₹100, got ₹{amount}"
        print("  ✓ 120 min = ₹100")
        
        # Test 4: 3 hours
        entry = datetime.now() - timedelta(hours=3)
        exit_t = datetime.now()
        amount, hours, billable = calc_amount(entry.isoformat(), exit_t.isoformat())
        assert amount == 150, f"Expected ₹150, got ₹{amount}"
        print("  ✓ 180 min = ₹150")
        
        print()
        return True
    except Exception as e:
        print(f"  ❌ Billing test failed: {e}")
        print()
        return False

def test_directories():
    """Test directory structure"""
    print("📁 Testing Directory Structure...")
    
    dirs = ['templates', 'static', 'captures', 'exports']
    all_ok = True
    
    for d in dirs:
        if Path(d).exists():
            print(f"  ✓ {d}/")
        else:
            Path(d).mkdir(parents=True, exist_ok=True)
            print(f"  ! Created {d}/")
    
    print()
    return True

def test_files():
    """Test required files"""
    print("📄 Testing Files...")
    
    files = [
        ('app_ui.py', 'Flask web app'),
        ('db.py', 'Database module'),
        ('billing.py', 'Billing module'),
        ('requirements.txt', 'Dependencies'),
        ('templates/dashboard.html', 'Dashboard'),
        ('templates/control_panel.html', 'Control panel'),
        ('templates/reports.html', 'Reports'),
    ]
    
    all_ok = True
    for file, desc in files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"  ✓ {desc:<20} ({size:,} bytes)")
        else:
            print(f"  ❌ {desc:<20} NOT FOUND")
            all_ok = False
    
    print()
    return all_ok

def test_flask():
    """Test Flask app loading"""
    print("🔌 Testing Flask App...")
    
    try:
        import app_ui
        print("  ✓ app_ui.py loads successfully")
        print(f"  ✓ Flask version: {app_ui.app.__class__.__module__}")
        print("  ✓ Routes registered:")
        
        for rule in app_ui.app.url_map.iter_rules():
            if 'static' not in rule.rule:
                methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
                print(f"      {rule.rule:<30} {methods}")
        
        print()
        return True
    except Exception as e:
        print(f"  ❌ Flask test failed: {e}")
        print()
        return False

def print_summary(results):
    """Print test summary"""
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print("="*70)
    print(f"📊 TEST SUMMARY: {passed}/{total} passed ({percentage:.0f}%)")
    print("="*70)
    print()
    
    if percentage == 100:
        print("✅ All tests passed! System is ready to run.\n")
        print("To start the system, run:")
        print("   python run_system.py")
        print("   or")
        print("   python app_ui.py")
        print()
    elif percentage >= 70:
        print("⚠️  Some tests failed. Check the output above.\n")
    else:
        print("❌ Multiple failures. Install dependencies:")
        print("   pip install -r requirements.txt\n")

def main():
    print_header()
    
    results = []
    
    # Run all tests
    results.append(test_imports())
    results.append(test_directories())
    results.append(test_files())
    results.append(test_database())
    results.append(test_billing())
    results.append(test_flask())
    
    print_summary(results)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
