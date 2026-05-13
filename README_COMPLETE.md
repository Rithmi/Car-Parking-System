# 🅿️ PARKING MANAGEMENT SYSTEM - COMPLETE INSTALLATION & USER GUIDE

**A professional, full-featured parking management system with modern web dashboard, real-time statistics, vehicle tracking, and automated billing.**

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start) - Get running in 5 minutes
2. [Installation](#-installation) - Detailed setup instructions
3. [Usage](#-usage) - How to use the system
4. [Features](#-features) - What's included
5. [API Documentation](#-api-documentation) - For developers
6. [Configuration](#-configuration) - Customization options
7. [Troubleshooting](#-troubleshooting) - Common issues
8. [System Architecture](#-system-architecture) - Technical overview

---

## 🚀 Quick Start

### For Windows Users
```bash
# Option 1: Double-click this file
START_SYSTEM.bat

# Option 2: Use command line
python run_system.py
```

### For Mac/Linux Users
```bash
# Option 1: Make executable and run
chmod +x start_system.sh
./start_system.sh

# Option 2: Direct Python
python3 run_system.py
```

### What Happens
- ✅ Checks Python installation
- ✅ Installs all dependencies
- ✅ Creates required directories
- ✅ Initializes database
- ✅ Starts web server
- ✅ Opens dashboard in browser

### Access the System
- **Dashboard:** http://localhost:5000
- **Control Panel:** http://localhost:5000/control
- **Reports:** http://localhost:5000/reports

---

## 💻 Installation

### System Requirements

- **Python:** 3.8 or higher
- **OS:** Windows, Mac, or Linux
- **RAM:** 512 MB minimum
- **Disk:** 100 MB available space
- **Browser:** Modern browser (Chrome, Firefox, Edge, Safari)

### Step 1: Check Python Installation

```bash
python --version    # Windows
# or
python3 --version   # Mac/Linux
```

Should show Python 3.8 or higher.

### Step 2: Install Dependencies

Option A - Automatic (recommended):
```bash
python run_system.py
```

Option B - Manual:
```bash
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python test_system.py
```

This will test all components and report any issues.

### Step 4: Generate Sample Data (Optional)

```bash
python generate_sample_data.py
```

This creates realistic test data for demonstrations.

### Step 5: Start the System

```bash
python app_ui.py
# or
python run_system.py
# or (Windows)
START_SYSTEM.bat
# or (Mac/Linux)
./start_system.sh
```

---

## 📱 Usage

### Dashboard

The main dashboard shows:
- **Real-time Statistics**
  - Cars currently in lot
  - Total exits
  - Revenue today
  - Average parking duration
  
- **Active Vehicles Table**
  - License plates
  - Entry times
  - Current duration
  
- **Recent Transactions**
  - Vehicle plates
  - Entry/exit times
  - Parking duration
  - Amount paid

- **Vehicle Search**
  - Search by license plate
  - View complete history
  - See all transactions

**Auto-Updates:** Every 10 seconds

### Control Panel

Administrative functions:
- **System Control**
  - Start/stop system
  - View system status
  - Monitor uptime

- **Camera Controls**
  - Test entry camera
  - Test exit camera
  - Configure camera IDs

- **Database Management**
  - Clear all data (with password)
  - Export to CSV
  - View statistics

- **System Logs**
  - Real-time log viewer
  - Filter by type
  - Export logs

**Auto-Updates:** Every 5 seconds

### Reports

Analytics and reporting features:
- **Daily Summary**
  - Total entries
  - Total exits
  - Revenue
  - Average duration

- **Hourly Revenue Chart**
  - Visual hourly breakdown
  - Revenue by time of day
  - Transaction counts

- **Transaction History**
  - Complete list of all exits
  - Filter options
  - Export to CSV

- **Currently Parked**
  - Active vehicles list
  - Entry times
  - Parking duration

**Auto-Updates:** Every 15 seconds

---

## ✨ Features

### Dashboard Features
- 📊 Real-time statistics cards
- 🚗 Active vehicles monitoring
- 💳 Transaction history
- 🔍 Advanced search by plate
- 📱 Responsive mobile design
- 🔄 Auto-refresh every 10 seconds
- 📈 Visual statistics display

### Control Panel Features
- 🎛️ System start/stop controls
- 💾 Database management
- 📷 Camera testing
- 🗑️ Data clearing with security
- 📥 CSV export
- 📝 Real-time system logs
- 🔧 Configuration options

### Reports Features
- 📊 Comprehensive daily summary
- 💹 Hourly revenue charts
- 💳 Complete transaction logs
- 📈 Analytics and trends
- 📥 Data export (CSV)
- 🔍 Advanced filtering
- 📱 Responsive layout

### Backend Features
- 🗄️ SQLite database
- 🔐 Data validation and security
- ⚡ High performance
- 🔄 Real-time updates
- 📊 Automatic calculations
- 💰 Tiered billing system
- 🚗 Vehicle tracking

---

## 🔌 API Documentation

All API endpoints return JSON responses.

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### Statistics
```
GET /api/stats
Response: {
  "cars_in_lot": 5,
  "total_entries": 42,
  "total_exits": 37,
  "revenue_today": 1850,
  "total_revenue": 45000,
  "avg_duration_minutes": 87.5,
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Active Vehicles
```
GET /api/vehicles/active
Response: {
  "count": 3,
  "vehicles": [
    {
      "id": 10,
      "plate": "QL9904",
      "entry_time": "2024-01-15T10:30:00",
      "duration_minutes": 120.5,
      "duration_formatted": "2.0 h"
    }
  ],
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Transactions
```
GET /api/transactions?limit=20
Response: {
  "count": 20,
  "transactions": [
    {
      "id": 100,
      "plate": "AB1234",
      "entry_time": "2024-01-15T10:00:00",
      "exit_time": "2024-01-15T11:30:00",
      "amount": 50,
      "duration_minutes": 90.0,
      "duration_formatted": "1.5 h",
      "date": "2024-01-15T11:30:00"
    }
  ],
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Vehicle Information
```
GET /api/vehicle/<PLATE>
Example: GET /api/vehicle/QL9904
Response: {
  "plate": "QL9904",
  "total_visits": 5,
  "records": [{ ... }],
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Vehicle Search
```
POST /api/search
Body: {"plate": "QL"}
Response: {
  "query": "QL",
  "count": 3,
  "results": ["QL9904", "QL1234", "QL5678"]
}
```

#### Hourly Revenue
```
GET /api/revenue/hourly
Response: {
  "data": [
    {"hour": "00:00", "revenue": 0, "transactions": 0},
    {"hour": "01:00", "revenue": 150, "transactions": 3},
    ...
  ],
  "timestamp": "2024-01-15T14:30:45"
}
```

#### System Logs
```
GET /api/logs?limit=50
Response: {
  "logs": ["[14:30:45] System started", ...],
  "count": 500,
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Health Check
```
GET /api/health
Response: {
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:45",
  "uptime": 1234567
}
```

#### System Status
```
GET /api/system/status
Response: {
  "running": true,
  "start_time": "2024-01-15T10:00:00",
  "cameras_active": {"entry": true, "exit": true},
  "uptime_seconds": 16245,
  "timestamp": "2024-01-15T14:30:45"
}
```

#### Export Data
```
GET /api/export/csv
Returns: CSV file with all data
```

#### Clear Database
```
POST /api/database/clear
Body: {"password": "admin123"}
Response: {"message": "Database cleared successfully"}
```

---

## 🔧 Configuration

### Change Port

Edit `app_ui.py`, line 307:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead of 5000
```

### Change Admin Password

Edit `app_ui.py`, line 262:
```python
if password != 'admin123':  # Change this!
    return jsonify({'error': 'Invalid password'}), 403
```

### Adjust Refresh Intervals

Edit `app_ui.py`:
```python
REFRESH_INTERVAL = 10000  # Dashboard refresh interval (ms)
MAX_LOGS = 500           # Maximum logs to keep
```

### Custom Billing Rates

Edit `billing.py`:
```python
RATE_PER_HOUR = 50           # Cost per hour
FREE_MINUTES = 55            # Free parking duration
TIER_1_MAX = 120             # 1 hour charge until
TIER_2_MAX = 180             # 2 hour charge until
TIER_2_RATE = 100            # Cost for 2 hours
TIER_3_RATE = 50             # Cost per additional hour
```

---

## 💰 Billing System

### Tiered Pricing Model

| Duration | Charge |
|----------|--------|
| 0-55 min | **FREE** ✅ |
| 56-120 min | **₹50** (1 hour) |
| 121-180 min | **₹100** (2 hours) |
| 181+ min | **₹100 + ₹50 per additional hour** |

### Examples

- **30 minutes:** ₹0 (FREE)
- **90 minutes:** ₹50
- **2 hours:** ₹100
- **3 hours:** ₹150 (₹100 + ₹50)
- **5 hours:** ₹250 (₹100 + ₹50×3)

---

## 🐛 Troubleshooting

### Port Already in Use

**Error:** "Address already in use"

**Solution:**
1. Change port in `app_ui.py` (line 307)
   ```python
   app.run(..., port=5001)
   ```
2. Or kill process using port 5000:
   - Windows: `netstat -ano | findstr :5000` then `taskkill /PID <number>`
   - Mac/Linux: `lsof -i :5000` then `kill <PID>`

### Database Locked

**Error:** "Database is locked"

**Solution:**
```bash
# Delete and recreate
rm parking.db
python run_system.py
```

### Module Not Found

**Error:** "No module named 'flask'"

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Flask Not Starting

**Error:** Application not starting

**Solution:**
1. Check terminal for specific error
2. Verify Python 3.8+: `python --version`
3. Test with: `python test_system.py`
4. Reinstall: `pip install -r requirements.txt`

### Dashboard Not Loading

**Error:** Blank page or connection error

**Solution:**
1. Check URL: http://localhost:5000
2. Check terminal - Flask should show "Running on"
3. Check firewall settings
4. Try different port (see "Port Already in Use")

### Slow Performance

**Solution:**
1. Reduce refresh intervals in JS
2. Limit transaction history limit
3. Clear old data regularly
4. Check system resources

---

## 📂 System Architecture

### File Structure

```
car_parking_lpr/
├── 🔴 Core Application Files
│   ├── app_ui.py                   ← Main Flask app (RUN THIS!)
│   ├── run_system.py               ← Automated startup script
│   ├── START_SYSTEM.bat            ← Windows startup
│   └── start_system.sh             ← Mac/Linux startup
│
├── 📦 Backend Modules
│   ├── db.py                       ← Database operations
│   ├── billing.py                  ← Billing calculations
│   ├── lpr.py                      ← License plate recognition
│   └── parking_system.py           ← Camera integration
│
├── 🎨 Frontend Templates
│   ├── templates/dashboard.html    ← Main dashboard
│   ├── templates/control_panel.html ← Admin control
│   └── templates/reports.html      ← Analytics & reports
│
├── 📁 Data & Configuration
│   ├── parking.db                  ← SQLite database
│   ├── requirements.txt            ← Python dependencies
│   ├── QUICKSTART.md              ← Quick start guide
│   ├── SETUP_GUIDE.md             ← Detailed setup
│   └── README.md                   ← This file
│
├── 📊 Utilities
│   ├── test_system.py              ← Component tests
│   ├── generate_sample_data.py     ← Sample data generator
│   └── check_db.py                 ← Database viewer
│
└── 📁 Runtime Directories
    ├── templates/                  ← HTML templates
    ├── static/                     ← CSS/JS (future use)
    ├── captures/                   ← Vehicle photos
    ├── exports/                    ← CSV exports
    └── model/                      ← ML models

```

### Technology Stack

- **Backend:** Flask (Python web framework)
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **API:** RESTful JSON endpoints
- **Styling:** Modern CSS with responsive design
- **Browser Support:** All modern browsers

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│            WEB BROWSER (Client)                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Dashboard / Control Panel / Reports         │  │
│  │  (HTML Templates + JavaScript)               │  │
│  └──────────────┬───────────────────────────────┘  │
└─────────────────┼────────────────────────────────────┘
                  │ HTTP/JSON
                  ▼
        ┌─────────────────────┐
        │   Flask App         │
        │ - API Endpoints     │
        │ - Route Handlers    │
        │ - Data Processing   │
        └──────────┬──────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌─────────┐         ┌──────────┐
    │Database │         │Billing   │
    │(SQLite) │         │Module    │
    └─────────┘         └──────────┘
```

---

## 🔐 Security

### Default Credentials

| Item | Default | Location |
|------|---------|----------|
| Admin Password | `admin123` | app_ui.py:262 |

**⚠️ Change these in production!**

### Data Protection

- ✅ Input validation on all endpoints
- ✅ SQLite database (local/secure)
- ✅ No sensitive data in logs
- ✅ CSV export is sanitized
- ✅ No authentication currently (add if needed)

### Recommendations for Production

1. Add user authentication
2. Use HTTPS (SSL certificate)
3. Change admin password
4. Set secure database path
5. Enable logging
6. Run behind reverse proxy (nginx)
7. Set strong SECRET_KEY
8. Enable CSRF protection

---

## 📊 Database Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    paid_amount INTEGER DEFAULT 0,
    status TEXT DEFAULT 'IN',
    entry_cam INTEGER,
    exit_cam INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plate ON sessions(plate);
CREATE INDEX idx_exit_time ON sessions(exit_time);
CREATE INDEX idx_status ON sessions(status);
```

---

## 📞 Support & FAQ

### Q: How do I change the port?
**A:** Edit `app_ui.py` line 307 and change port number.

### Q: Can I run on a different network?
**A:** Change `localhost` to `0.0.0.0` - already set by default!

### Q: How do I backup my data?
**A:** Copy `parking.db` file to a backup location.

### Q: Can I integrate with real cameras?
**A:** Yes, integrate with `parking_system.py` which handles OpenCV.

### Q: What if I lose my data?
**A:** If you cleared the database, run `generate_sample_data.py` to recreate test data.

### Q: Is there a mobile app?
**A:** Not yet, but the web UI is fully responsive for mobile browsers.

### Q: Can multiple users access it simultaneously?
**A:** Yes! Flask supports concurrent requests.

---

## 🎓 Learning Resources

- **Flask:** https://flask.palletsprojects.com/
- **SQLite:** https://www.sqlite.org/docs.html
- **JavaScript Fetch:** https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- **Bootstrap CSS:** https://getbootstrap.com/

---

## 📜 License

This project is for parking management use only.

---

## ✅ Checklist for First Run

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test passed (`python test_system.py`)
- [ ] Sample data generated (`python generate_sample_data.py`)
- [ ] System started (`python app_ui.py`)
- [ ] Dashboard accessible (http://localhost:5000)
- [ ] Can view statistics
- [ ] Can search vehicles
- [ ] Can export data

---

## 🚀 Next Steps

1. **Explore the Dashboard**
   - Check real-time statistics
   - Search for vehicles
   - View transactions

2. **Test Admin Controls**
   - View system status
   - Export data
   - Check logs

3. **Review Reports**
   - Check daily summary
   - View hourly revenue
   - Analyze trends

4. **Integrate with Cameras**
   - Connect entry/exit cameras
   - Configure LPR
   - Test vehicle detection

5. **Deploy to Production**
   - Set up HTTPS
   - Configure domain
   - Add authentication
   - Set up monitoring

---

**🅿️ Thank you for using Parking Management System!**

For issues or questions, check the logs or review this documentation.

Happy Parking! 🚗✨
