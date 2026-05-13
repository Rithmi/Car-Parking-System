#!/usr/bin/env python3
"""
PARKING MANAGEMENT SYSTEM - COMPLETE SETUP & RUN GUIDE
========================================================

This script sets up and runs the complete parking management system with web UI.

Requirements:
- Python 3.8+
- pip (Python package manager)

Run: python run_system.py
"""

import os
import sys
import subprocess
import webbrowser
import platform
import time
from pathlib import Path

def print_header():
    """Print system header"""
    print("\n" + "="*70)
    print("🅿️ PARKING MANAGEMENT SYSTEM - COMPLETE SETUP")
    print("="*70 + "\n")

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8 or higher required")
        print(f"Your version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing Dependencies...\n")
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("⚠️  requirements.txt not found!")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-q', '-r', str(requirements_file)
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("Run manually: pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating Directories...\n")
    dirs = ['templates', 'static', 'captures', 'exports', 'model']
    
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"✓ {d}/")

def check_database():
    """Initialize database if needed"""
    print("\n💾 Initializing Database...\n")
    
    try:
        import db
        db.init_db()
        print("✅ Database ready!")
        return True
    except Exception as e:
        print(f"⚠️  Database issue: {e}")
        return True  # Continue anyway

def open_browser(url, delay=2):
    """Open browser after delay"""
    print(f"\n⏳ Opening browser in {delay} seconds...")
    time.sleep(delay)
    
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', url])
        elif platform.system() == 'Windows':
            os.startfile(url)
        else:  # Linux
            subprocess.Popen(['xdg-open', url])
    except:
        pass

def main():
    """Main setup and run function"""
    print_header()
    
    # Step 1: Check Python
    print("🔍 Checking Environment...\n")
    check_python_version()
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Install dependencies
    install_dependencies()
    
    # Step 4: Initialize database
    check_database()
    
    # Step 5: Run Flask app
    print("\n" + "="*70)
    print("🚀 STARTING WEB SERVER")
    print("="*70)
    print("\n📱 Dashboard:    http://localhost:5000/")
    print("🎛️  Control:      http://localhost:5000/control")
    print("📊 Reports:      http://localhost:5000/reports")
    print("🔌 API Base:     http://localhost:5000/api")
    print("\n⏹️  To stop: Press Ctrl+C\n")
    print("="*70 + "\n")
    
    # Open browser in background
    import threading
    browser_thread = threading.Thread(target=lambda: open_browser('http://localhost:5000'), daemon=True)
    browser_thread.start()
    
    # Run Flask app
    try:
        os.system(f'{sys.executable} app_ui.py')
    except KeyboardInterrupt:
        print("\n\n⏹️  System stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
