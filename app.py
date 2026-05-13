"""
PARKING SYSTEM - WEB DASHBOARD
Flask-based web interface for parking management
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import db
from billing import calc_amount

app = Flask(__name__)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_parking_stats():
    """Get parking statistics"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Cars currently in lot
    cur.execute("SELECT COUNT(*) as count FROM sessions WHERE status='IN'")
    cars_in = cur.fetchone()['count']
    
    # Total exits today
    today = datetime.now().date()
    today_str = today.isoformat()
    cur.execute(
        "SELECT COUNT(*) as count FROM sessions WHERE status='OUT' AND date(exit_time)=?",
        (today_str,)
    )
    exits_today = cur.fetchone()['count']
    
    # Total revenue today
    cur.execute(
        "SELECT SUM(paid_amount) as total FROM sessions WHERE status='OUT' AND date(exit_time)=? AND paid_amount > 0",
        (today_str,)
    )
    revenue_today = cur.fetchone()['total'] or 0.0
    
    # Total all-time revenue
    cur.execute("SELECT SUM(paid_amount) as total FROM sessions WHERE paid_amount > 0")
    total_revenue = cur.fetchone()['total'] or 0.0
    
    conn.close()
    
    return {
        'cars_in': cars_in,
        'exits_today': exits_today,
        'revenue_today': revenue_today,
        'total_revenue': total_revenue
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """Get parking statistics"""
    stats = get_parking_stats()
    return jsonify(stats)

@app.route('/api/active-vehicles')
def api_active_vehicles():
    """Get currently active vehicles"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, plate, entry_time 
        FROM sessions 
        WHERE status='IN' 
        ORDER BY entry_time DESC
    """)
    
    vehicles = []
    for row in cur.fetchall():
        entry_dt = datetime.fromisoformat(row['entry_time'])
        now = datetime.now()
        duration = (now - entry_dt).total_seconds()
        
        vehicles.append({
            'id': row['id'],
            'plate': row['plate'],
            'entry_time': row['entry_time'],
            'duration_minutes': int(duration / 60),
            'duration_hours': duration / 3600
        })
    
    conn.close()
    return jsonify(vehicles)

@app.route('/api/recent-exits')
def api_recent_exits():
    """Get recent exit transactions"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, plate, entry_time, exit_time, paid_amount 
        FROM sessions 
        WHERE status='OUT' 
        ORDER BY exit_time DESC 
        LIMIT 10
    """)
    
    exits = []
    for row in cur.fetchall():
        entry_dt = datetime.fromisoformat(row['entry_time'])
        exit_dt = datetime.fromisoformat(row['exit_time'])
        duration = (exit_dt - entry_dt).total_seconds() / 3600
        
        exits.append({
            'plate': row['plate'],
            'entry_time': row['entry_time'],
            'exit_time': row['exit_time'],
            'duration_hours': round(duration, 2),
            'amount': round(row['paid_amount'], 2)
        })
    
    conn.close()
    return jsonify(exits)

@app.route('/api/manual-entry', methods=['POST'])
def api_manual_entry():
    """Manual entry for testing"""
    data = request.json
    plate = data.get('plate', '').strip().upper()
    
    if not plate:
        return jsonify({'success': False, 'message': 'Plate cannot be empty'}), 400
    
    ok, msg = db.start_parking(plate)
    return jsonify({
        'success': ok,
        'message': msg,
        'plate': plate
    })

@app.route('/api/manual-exit', methods=['POST'])
def api_manual_exit():
    """Manual exit for testing"""
    data = request.json
    plate = data.get('plate', '').strip().upper()
    
    if not plate:
        return jsonify({'success': False, 'message': 'Plate cannot be empty'}), 400
    
    # Get entry time
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT entry_time FROM sessions WHERE plate=? AND status='IN' ORDER BY id DESC LIMIT 1",
        (plate,)
    )
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return jsonify({
            'success': False,
            'message': f'No active entry found for {plate}'
        }), 404
    
    entry_time = row['entry_time']
    exit_time = datetime.now().isoformat(timespec='seconds')
    amount, actual_hours, billed_hours = calc_amount(entry_time, exit_time)
    
    ok, msg = db.end_parking(plate, amount)
    
    return jsonify({
        'success': ok,
        'message': msg,
        'plate': plate,
        'entry_time': entry_time,
        'exit_time': exit_time,
        'duration_hours': round(actual_hours, 2),
        'billable_hours': billed_hours,
        'amount': round(amount, 2)
    })

if __name__ == '__main__':
    db.init_db()
    print("\n" + "="*60)
    print("  🅿️  PARKING SYSTEM - WEB DASHBOARD")
    print("="*60)
    print("\n  🌐 Starting web server...")
    print("  📍 Visit: http://localhost:5000")
    print("\n  Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    app.run(debug=True, host='localhost', port=5000)
