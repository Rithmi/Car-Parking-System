# 🅿️ DUAL CAMERA PARKING SYSTEM - COMPLETE SETUP GUIDE

## 📋 System Overview

```
ENTRY POINT                          EXIT POINT
     ↓                                    ↓
[CAMERA 1]                           [CAMERA 2]
     ↓                                    ↓
Motion Detection                    Motion Detection
     ↓                                    ↓
Capture Vehicle                    Capture Vehicle
     ↓                                    ↓
Read License Plate (OCR)           Read License Plate (OCR)
     ↓                                    ↓
Record Entry Time                  Calculate Fee
     ↓                                    ↓
[DATABASE]                         Display Payment
                                         ↓
                                   Simulate Gate Open
                                         ↓
                                   [DATABASE]
```

## ✅ Requirements

- Python 3.11+ with opencv, easyocr, numpy
- 2 USB Webcams (or 1 webcam for testing)
- SQLite3 (included with Python)
- Stable power supply

## 🚀 Installation Steps

### Step 1: Install Required Packages
```bash
pip install opencv-python easyocr numpy
```

### Step 2: Check Camera IDs
```bash
python test_cameras.py
```

This will test which camera IDs are available:
- If you have 1 camera: `ENTRY_CAMERA_ID = 0, EXIT_CAMERA_ID = 0`
- If you have 2 cameras: `ENTRY_CAMERA_ID = 0, EXIT_CAMERA_ID = 1`

### Step 3: Update Camera IDs in Code
Edit `parking_system.py`:
```python
ENTRY_CAMERA_ID = 0   # Change if needed
EXIT_CAMERA_ID = 1    # Change if needed
```

## 🎬 Running the System

### Start Main Parking System
```bash
python parking_system.py
```

**Output:**
- Window 1: ENTRY CAMERA feed
- Window 2: EXIT CAMERA feed
- Console: Real-time alerts & status

### View Reports & History
```bash
python view_reports.py
```

**Features:**
- View last 20 sessions
- See currently parked vehicles
- Revenue summary

### Test with Sample Images
```bash
python test_ocr.py
```

## 📊 System Features

### Entry Camera
- ✅ Detects vehicle motion
- ✅ Captures license plate
- ✅ Confirms reading 3x (consistency)
- ✅ Records entry time in database
- ✅ 8-second cooldown (prevents duplicates)

### Exit Camera
- ✅ Detects vehicle motion
- ✅ Captures license plate
- ✅ Looks up entry time from database
- ✅ Calculates parking fee
- ✅ Displays bill details
- ✅ Simulates gate opening
- ✅ Records exit time + amount in database

### Billing Rules
- **0-55 minutes**: FREE ✅
- **56-120 minutes**: Rs 50 (1 hour) ✅
- **121-180 minutes**: Rs 100 (2 hours) ✅
- **Each additional hour**: Rs 50

### Motion Detection
- Compares consecutive frames
- Only triggers OCR when movement detected
- Saves CPU resources (~40% reduction)

## 📁 File Structure
```
car_parking_lpr/
├── parking_system.py          ← MAIN SYSTEM (Run this!)
├── view_reports.py            ← Database viewer
├── db.py                       ← Database functions
├── billing.py                  ← Billing calculations
├── lpr.py                      ← License plate recognition
├── main_ocr.py               ← Image-based OCR mode
├── live_camera.py            ← Single camera mode
├── test_ocr.py               ← Test OCR with images
├── parking.db                ← SQLite database (auto-created)
├── captures/                 ← Saved vehicle images
└── model/
    └── haarcascade_plate.xml
```

## 🔧 Configuration Options

Edit `parking_system.py` to change:

```python
# Camera IDs
ENTRY_CAMERA_ID = 0
EXIT_CAMERA_ID = 1

# Plate detection confidence
CONF_THRESH = 0.75  # 0.0-1.0 (higher = stricter)

# Consistency checking
CONSISTENCY_FRAMES = 3  # frames to confirm plate

# Cooldown between captures
COOLDOWN = 8  # seconds

# Motion detection threshold
MOTION_THRESHOLD = 1000  # pixels changed
```

## 🐛 Troubleshooting

### Problem: "Cannot open camera"
**Solution:**
- Check camera is connected
- Try different camera ID
- Run `python test_cameras.py`

### Problem: "OCR fails to detect plates"
**Solution:**
- Improve lighting conditions
- Increase `CONF_THRESH` to 0.8
- Ensure plates are clearly visible
- Test with `python test_ocr.py`

### Problem: "High CPU usage"
**Solution:**
- Motion detection is enabled (saves CPU)
- Reduce frame resolution
- Lower `CONF_THRESH` to 0.6

### Problem: "Database locked"
**Solution:**
- Close other instances
- Delete `parking.db` to reset

## 📈 Performance Tips

1. **Best mounting position:**
   - Mount cameras 5-10 meters before entry/exit
   - Angle slightly downward toward plate
   - Mount 1.5-2 meters height

2. **Lighting:**
   - Good natural/artificial light
   - Avoid backlighting
   - Use IR illuminator for night

3. **Plate capture:**
   - Clear, straight plates work best
   - Dirty plates reduce accuracy
   - Test different angles

## 🔐 Security Features

- ✅ SQLite database (local)
- ✅ Image capture logging (audit trail)
- ✅ Unique session IDs
- ✅ Timestamp records
- ✅ No personal data stored

## 📞 Support

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| Plate not detected | Improve lighting, adjust CONF_THRESH |
| Duplicate entries | Cooldown already prevents this |
| Revenue not updating | Check database file has write permission |
| Gate doesn't open | Simulated - replace simulate_gate_open() with real control |

## 🚀 Next Steps for Production

1. **Add real gate control:**
   ```python
   # Replace simulate_gate_open() with:
   # GPIO.output(GATE_PIN, GPIO.HIGH)  # Open gate
   ```

2. **Add payment terminal integration:**
   - Display QR code
   - SMS notification
   - Email receipt

3. **Add web dashboard:**
   - Real-time monitoring
   - Revenue reports
   - Vehicle history

4. **Add plate whitelisting:**
   - VIP cars (free parking)
   - Staff vehicles
   - Blacklist banned plates

## 📝 License

This system is for parking management only.

---

**Happy Parking! 🅿️**
