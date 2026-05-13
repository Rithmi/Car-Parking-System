# 🅿️ PARKING MANAGEMENT SYSTEM - COMPLETE WEB UI

A fully functional parking management system with professional web dashboard, real-time statistics, vehicle tracking, and billing calculations.

## 🚀 Quick Start (5 Minutes)

### Option 1: Automatic Setup (Recommended)
```bash
python run_system.py
```
This will:
- ✅ Check Python version
- ✅ Install dependencies
- ✅ Create directories
- ✅ Initialize database
- ✅ Start web server
- ✅ Open dashboard in your browser

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask web app
python app_ui.py
```

## 📱 Web Interfaces

### 1. **Dashboard** (http://localhost:5000)
- Real-time statistics (cars in lot, exits, revenue)
- Active vehicles list
- Recent transactions
- Vehicle search by plate number
- Auto-refresh every 10 seconds

### 2. **Control Panel** (http://localhost:5000/control)
- System status monitoring
- Start/Stop controls
- Camera testing
- Database management
- System logs viewer
- Stats refresh controls

### 3. **Reports** (http://localhost:5000/reports)
- Daily summary cards
- Hourly revenue chart
- Transaction history
- Currently parked vehicles
- CSV export functionality
- Transaction filtering

## 🔌 API Endpoints

All endpoints return JSON:

```
GET  /api/stats                 → Current statistics
GET  /api/vehicles/active       → Cars in parking lot
GET  /api/transactions          → Recent exit records
GET  /api/revenue/hourly        → Hourly revenue data
GET  /api/vehicle/<plate>       → Vehicle details by plate
GET  /api/search                → Search vehicles by plate (POST with JSON)
GET  /api/logs                  → System logs
GET  /api/health                → API health check
POST /api/database/clear        → Clear all data (needs password)
GET  /api/export/csv            → Download CSV export
```

### Example API Calls

```javascript
// Get current statistics
fetch('/api/stats')
  .then(r => r.json())
  .then(data => console.log(data));

// Get active vehicles
fetch('/api/vehicles/active')
  .then(r => r.json())
  .then(data => console.log(data.vehicles));

// Search vehicle
fetch('/api/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({plate: 'QL9904'})
})
.then(r => r.json())
.then(data => console.log(data));
```

## 📊 Database Schema

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    plate TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    paid_amount INTEGER DEFAULT 0,
    status TEXT DEFAULT 'IN',  -- 'IN' or 'OUT'
    entry_cam INTEGER,
    exit_cam INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 💰 Billing Rules

- **0-55 minutes**: FREE ✅
- **56-120 minutes**: ₹50
- **121-180 minutes**: ₹100
- **181+ minutes**: ₹100 + ₹50 per additional hour

Example:
```python
from billing import calc_amount

entry = "2024-01-15T10:00:00"
exit = "2024-01-15T11:30:00"  # 90 minutes

amount, duration_hours, billable_hours = calc_amount(entry, exit)
# Returns: (50, 1.5, 1)  → ₹50 for 1.5 hours
```

## 🎯 Features

### Dashboard Features
- 📊 Real-time statistics cards
- 🚗 Active vehicles table
- 💳 Recent transactions with amounts
- 🔍 Search by license plate
- 📱 Auto-refresh every 10 seconds
- 📱 Responsive mobile design

### Control Panel Features
- 🔧 System status monitoring
- ⚙️ Start/Stop controls
- 📷 Camera test controls
- 💾 Database management
- 🗑️ Clear database with password
- 📥 Export to CSV
- 📝 Real-time system logs

### Reports Features
- 📈 Daily summary statistics
- 💹 Hourly revenue chart
- 💳 Complete transaction history
- 🚗 Currently parked vehicles list
- 📥 Filter and export options
- 📊 Revenue calculations

## 🔐 Security Notes

- Default admin password for clearing database: `admin123`
- ⚠️ Change this in `app_ui.py` line 262
- All database operations are protected
- CSV exports sanitized properly
- No sensitive data in logs

## 📂 Project Structure

```
car_parking_lpr/
├── app_ui.py                 ← Main Flask web app (RUN THIS)
├── run_system.py             ← Automated startup script
├── db.py                     ← Database module
├── billing.py                ← Billing calculations
├── lpr.py                    ← License plate recognition
├── parking_system.py         ← Camera system
├── requirements.txt          ← Python dependencies
├── parking.db                ← SQLite database
├── templates/
│   ├── dashboard.html        ← Main dashboard
│   ├── control_panel.html    ← Control panel
│   └── reports.html          ← Reports page
├── static/                   ← CSS, JS (future)
├── captures/                 ← Vehicle photos
├── exports/                  ← CSV exports
└── QUICKSTART.md            ← This file
```

## 🔧 Configuration

Edit `app_ui.py` to customize:

```python
# Line 14: Change refresh interval (milliseconds)
REFRESH_INTERVAL = 10000

# Line 262: Change admin password
if password != 'admin123':  # Change this!

# Add more configurations as needed
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in app_ui.py last line
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Database Locked
```bash
# Delete and recreate database
rm parking.db
python run_system.py
```

### Module Not Found
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Dashboard Not Loading
- Check console for errors
- Verify Flask is running (check terminal)
- Try http://localhost:5000
- Check firewall settings

## 📝 Sample Data

To test the system with sample data:

```python
# In Python shell or script
import db
from datetime import datetime, timedelta

db.init_db()

# Add sample entry
success, msg = db.start_parking('QL9904', 0)
print(msg)

# Add sample exit 2 hours later
from billing import calc_amount
amount, hours, billable = calc_amount(
    datetime.now().isoformat(),
    (datetime.now() + timedelta(hours=2)).isoformat()
)
success, msg = db.end_parking('QL9904', amount, 1)
print(msg)
```

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_ui:app
```

### Using Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app_ui.py"]
```

### Environment Variables
```bash
export FLASK_ENV=production
export FLASK_DEBUG=False
python app_ui.py
```

## 📊 API Response Examples

### GET /api/stats
```json
{
  "cars_in_lot": 5,
  "total_entries": 42,
  "total_exits": 37,
  "revenue_today": 1850,
  "total_revenue": 45000,
  "avg_duration_minutes": 87.5,
  "timestamp": "2024-01-15T14:30:45"
}
```

### GET /api/vehicles/active
```json
{
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

### GET /api/transactions
```json
{
  "count": 15,
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

## 🎓 Learning Resources

- Flask Documentation: https://flask.palletsprojects.com/
- SQLite Docs: https://www.sqlite.org/docs.html
- JavaScript Fetch API: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- HTML5 Date Time: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/datetime-local

## 📞 Support

If you encounter issues:

1. Check the error message in browser console (F12)
2. Look at terminal where Flask is running
3. Check `parking.db` exists and is readable
4. Verify all dependencies installed: `pip list | grep -i flask`
5. Try clearing browser cache

## 🔄 Continuous Integration

The system auto-refreshes:
- Dashboard: Every 10 seconds
- Control Panel: Every 5 seconds
- Reports: Every 15 seconds

All statistics update in real-time as vehicles enter/exit.

## 📄 License

This project is for parking management only. Please use responsibly.

## 🎯 Future Enhancements

- [ ] WebSocket for real-time updates
- [ ] Email notifications
- [ ] SMS payment integration
- [ ] Mobile app
- [ ] QR code generation
- [ ] Advanced analytics
- [ ] Multi-site support
- [ ] User authentication

---

**Happy Parking! 🅿️**

For more detailed setup guide, see SETUP_GUIDE.md
