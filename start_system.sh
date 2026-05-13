#!/bin/bash

# =====================================================
# PARKING MANAGEMENT SYSTEM - Linux/Mac Startup Script
# =====================================================
#
# This script sets up and runs the complete parking
# management system on Linux/Mac.
#
# Usage: bash start_system.sh  or  ./start_system.sh
# If using ./start_system.sh, first run: chmod +x start_system.sh
# =====================================================

set -e

echo ""
echo "====================================================="
echo "  PARKING MANAGEMENT SYSTEM - STARTUP"
echo "====================================================="
echo ""

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "On macOS: brew install python3"
    echo "On Ubuntu: sudo apt-get install python3 python3-pip"
    exit 1
fi

echo "[OK] Python found: $(python3 --version)"

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p templates static captures exports
echo "[OK] Directories created"

# Install dependencies
echo ""
echo "Installing dependencies..."
python3 -m pip install -q -r requirements.txt 2>/dev/null || true
echo "[OK] Dependencies ready"

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "import db; db.init_db()" 2>/dev/null || true
echo "[OK] Database ready"

# Display information
echo ""
echo "====================================================="
echo "  STARTING WEB SERVER"
echo "====================================================="
echo ""
echo "   Dashboard:    http://localhost:5000/"
echo "   Control:      http://localhost:5000/control"
echo "   Reports:      http://localhost:5000/reports"
echo ""
echo "   To stop: Press Ctrl+C"
echo ""
echo "====================================================="
echo ""

# Start Flask
python3 app_ui.py

echo ""
echo "System stopped."
