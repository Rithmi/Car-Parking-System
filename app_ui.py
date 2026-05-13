"""
PARKING MANAGEMENT SYSTEM - FLASK WEB UI
=========================================
Complete web-based control panel and dashboard with real-time updates.
Serves both admin panel and user-facing dashboard.

RUN: python app_ui.py
VISIT: http://localhost:5000

Features:
- Real-time statistics
- Vehicle entry/exit tracking
- Billing display
- Live camera feed display
- Reports and history
- Admin controls
- RESTful API endpoints
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from flask_cors import CORS
import sqlite3
import json
import threading
import subprocess
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import db
from billing import calc_amount

# ============== FLASK APP INITIALIZATION ==============
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# Global state
system_state = {
    'running': False,
    'process': None,
    'start_time': None,
    'last_update': None,
    'cameras_active': {'entry': False, 'exit': False}
}

log_buffer = []
MAX_LOGS = 500

def add_log(message: str):
    """Add message to log buffer"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    log_buffer.append(log_entry)
    if len(log_buffer) > MAX_LOGS:
        log_buffer.pop(0)
    print(log_entry)

# ============== STATISTICS FUNCTIONS ==============

def get_parking_stats() -> Dict:
    """Get current parking statistics"""
    try:
        with db.get_db() as conn:
            cur = conn.cursor()
            
            # Cars currently in lot
            cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'IN'")
            cars_in_lot = cur.fetchone()[0]
            
            # Total entries
            cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'IN' OR status = 'OUT'")
            total_entries = cur.fetchone()[0]
            
            # Total exits
            cur.execute("SELECT COUNT(*) FROM sessions WHERE status = 'OUT'")
            total_exits = cur.fetchone()[0]
            
            # Today's revenue
            today = datetime.now().strftime('%Y-%m-%d')
            cur.execute(
                "SELECT COALESCE(SUM(paid_amount), 0) FROM sessions WHERE status = 'OUT' AND created_at LIKE ?",
                (f"{today}%",)
            )
            revenue_today = cur.fetchone()[0]
            
            # Total revenue
            cur.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM sessions WHERE status = 'OUT'")
            total_revenue = cur.fetchone()[0]
            
            # Average stay duration
            cur.execute(
                """SELECT AVG((julianday(exit_time) - julianday(entry_time)) * 24 * 60) 
                   FROM sessions WHERE exit_time IS NOT NULL"""
            )
            avg_duration = cur.fetchone()[0] or 0
            
            return {
                'cars_in_lot': cars_in_lot,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'revenue_today': int(revenue_today),
                'total_revenue': int(total_revenue),
                'avg_duration_minutes': round(avg_duration, 1),
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        add_log(f"ERROR getting stats: {str(e)}")
        return {
            'cars_in_lot': 0,
            'total_entries': 0,
            'total_exits': 0,
            'revenue_today': 0,
            'total_revenue': 0,
            'avg_duration_minutes': 0,
            'timestamp': datetime.now().isoformat()
        }

def get_active_vehicles() -> List[Dict]:
    """Get all vehicles currently in parking lot"""
    try:
        with db.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, plate, entry_time, 
                   (julianday('now') - julianday(entry_time)) * 24 * 60 as duration_minutes
                   FROM sessions WHERE status = 'IN'
                   ORDER BY entry_time DESC"""
            )
            
            vehicles = []
            for row in cur.fetchall():
                entry_time = datetime.fromisoformat(row[2])
                duration_mins = row[3]
                
                vehicles.append({
                    'id': row[0],
                    'plate': row[1],
                    'entry_time': row[2],
                    'duration_minutes': round(duration_mins, 1),
                    'duration_formatted': format_duration(duration_mins)
                })
            
            return vehicles
    except Exception as e:
        add_log(f"ERROR getting active vehicles: {str(e)}")
        return []

def get_recent_transactions() -> List[Dict]:
    """Get recent exit transactions (last 20)"""
    try:
        with db.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, plate, entry_time, exit_time, paid_amount, created_at
                   FROM sessions WHERE status = 'OUT'
                   ORDER BY exit_time DESC LIMIT 20"""
            )
            
            transactions = []
            for row in cur.fetchall():
                try:
                    entry_time = datetime.fromisoformat(row[2])
                    exit_time = datetime.fromisoformat(row[3])
                    duration_mins = (exit_time - entry_time).total_seconds() / 60
                    
                    transactions.append({
                        'id': row[0],
                        'plate': row[1],
                        'entry_time': row[2],
                        'exit_time': row[3],
                        'amount': row[4],
                        'duration_minutes': round(duration_mins, 1),
                        'duration_formatted': format_duration(duration_mins),
                        'date': row[5]
                    })
                except:
                    continue
            
            return transactions
    except Exception as e:
        add_log(f"ERROR getting transactions: {str(e)}")
        return []

def format_duration(minutes: float) -> str:
    """Format duration in readable format"""
    if minutes < 60:
        return f"{int(minutes)} min"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f} h"
    days = hours / 24
    return f"{days:.1f} d"

def get_hourly_revenue() -> List[Dict]:
    """Get revenue by hour for today"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with db.get_db() as conn:
            cur = conn.cursor()
            
            hourly_data = []
            for hour in range(24):
                start_time = f"{today} {hour:02d}:00:00"
                end_time = f"{today} {hour:02d}:59:59"
                
                cur.execute(
                    """SELECT COALESCE(SUM(paid_amount), 0), COUNT(*)
                       FROM sessions WHERE status = 'OUT' 
                       AND exit_time >= ? AND exit_time <= ?""",
                    (start_time, end_time)
                )
                
                result = cur.fetchone()
                revenue = result[0] if result else 0
                count = result[1] if result else 0
                
                hourly_data.append({
                    'hour': f"{hour:02d}:00",
                    'revenue': int(revenue),
                    'transactions': count
                })
            
            return hourly_data
    except Exception as e:
        add_log(f"ERROR getting hourly revenue: {str(e)}")
        return []

# ============== ROUTES - PAGES ==============

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/control')
def control_panel():
    """Admin control panel"""
    return render_template('control_panel.html')

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

# ============== ROUTES - API ==============

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get parking statistics"""
    return jsonify(get_parking_stats())

@app.route('/api/vehicles/active', methods=['GET'])
def api_active_vehicles():
    """Get active vehicles in lot"""
    vehicles = get_active_vehicles()
    return jsonify({
        'count': len(vehicles),
        'vehicles': vehicles,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/transactions', methods=['GET'])
def api_transactions():
    """Get recent transactions"""
    limit = request.args.get('limit', 20, type=int)
    transactions = get_recent_transactions()[:limit]
    return jsonify({
        'count': len(transactions),
        'transactions': transactions,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/revenue/hourly', methods=['GET'])
def api_hourly_revenue():
    """Get hourly revenue data for today"""
    data = get_hourly_revenue()
    return jsonify({
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/system/status', methods=['GET'])
def api_system_status():
    """Get system status"""
    return jsonify({
        'running': system_state['running'],
        'start_time': system_state['start_time'],
        'cameras_active': system_state['cameras_active'],
        'uptime_seconds': int((datetime.now() - datetime.fromisoformat(system_state['start_time'])).total_seconds()) if system_state['start_time'] else 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/vehicle/<plate>', methods=['GET'])
def api_vehicle_info(plate):
    """Get vehicle information by plate"""
    try:
        plate = plate.upper()
        with db.get_db() as conn:
            cur = conn.cursor()
            
            # Get all records for this plate
            cur.execute(
                """SELECT id, plate, entry_time, exit_time, paid_amount, status, created_at
                   FROM sessions WHERE UPPER(plate) = ?
                   ORDER BY created_at DESC""",
                (plate,)
            )
            
            records = []
            for row in cur.fetchall():
                try:
                    entry_time = datetime.fromisoformat(row[2])
                    exit_time = datetime.fromisoformat(row[3]) if row[3] else None
                    
                    if exit_time:
                        duration_mins = (exit_time - entry_time).total_seconds() / 60
                    else:
                        duration_mins = (datetime.now() - entry_time).total_seconds() / 60
                    
                    records.append({
                        'id': row[0],
                        'plate': row[1],
                        'entry_time': row[2],
                        'exit_time': row[3],
                        'amount_paid': row[4],
                        'status': row[5],
                        'duration_minutes': round(duration_mins, 1),
                        'date': row[6]
                    })
                except:
                    continue
            
            return jsonify({
                'plate': plate,
                'total_visits': len(records),
                'records': records,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/search', methods=['POST'])
def api_search():
    """Search vehicles by plate"""
    data = request.get_json()
    plate = data.get('plate', '').upper()
    
    if not plate or len(plate) < 2:
        return jsonify({'error': 'Plate must be at least 2 characters'}), 400
    
    try:
        with db.get_db() as conn:
            cur = conn.cursor()
            
            # Search for matching plates
            cur.execute(
                """SELECT DISTINCT plate FROM sessions 
                   WHERE UPPER(plate) LIKE ?
                   ORDER BY plate""",
                (f"%{plate}%",)
            )
            
            results = [row[0] for row in cur.fetchall()]
            return jsonify({
                'query': plate,
                'count': len(results),
                'results': results
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """Get system logs"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'logs': log_buffer[-limit:],
        'count': len(log_buffer),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/database/clear', methods=['POST'])
def api_clear_database():
    """Clear database (ADMIN ONLY)"""
    password = request.json.get('password', '')
    if password != 'admin123':  # Change this to a secure password
        return jsonify({'error': 'Invalid password'}), 403
    
    try:
        if os.path.exists('parking.db'):
            os.remove('parking.db')
            db.init_db()
            add_log("Database cleared by admin")
            return jsonify({'message': 'Database cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def api_export_csv():
    """Export data as CSV"""
    try:
        with db.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, plate, entry_time, exit_time, paid_amount, status, created_at
                   FROM sessions ORDER BY created_at DESC"""
            )
            
            lines = ['ID,PLATE,ENTRY_TIME,EXIT_TIME,AMOUNT_RS,STATUS,DATE']
            for row in cur.fetchall():
                lines.append(f'{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]}')
            
            csv_content = '\n'.join(lines)
            
            # Create a temporary file
            filename = f'parking_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            filepath = os.path.join('exports', filename)
            
            os.makedirs('exports', exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(csv_content)
            
            return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': int(time.time())
    })

# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============== INITIALIZATION ==============

if __name__ == '__main__':
    # Initialize database
    db.init_db()
    add_log("Parking Management System Started")
    add_log("Visiting http://localhost:5000")
    
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    # Run Flask app
    print("\n" + "="*60)
    print("🅿️ PARKING MANAGEMENT SYSTEM - WEB UI")
    print("="*60)
    print("📱 Dashboard: http://localhost:5000")
    print("🎛️ Control Panel: http://localhost:5000/control")
    print("📊 Reports: http://localhost:5000/reports")
    print("🔌 API: http://localhost:5000/api/stats")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
