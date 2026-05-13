"""
SQLite database module for parking system.
Manages sessions table with entry/exit records.
"""

import sqlite3
from contextlib import contextmanager
from typing import Tuple, List, Dict, Optional
from datetime import datetime

DB_NAME = "parking.db"

# SQL Schema
SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
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
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_plate ON sessions(plate);",
    "CREATE INDEX IF NOT EXISTS idx_exit_time ON sessions(exit_time);",
    "CREATE INDEX IF NOT EXISTS idx_status ON sessions(status);",
]


@contextmanager
def get_db():
    """Context manager for safe database connections."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.execute(SESSIONS_TABLE)
        for idx in INDEXES:
            conn.execute(idx)
        # Ensure new columns exist for older DBs (migration)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(sessions)")
            existing = {row[1] for row in cur.fetchall()}  # name is at index 1

            # Columns we expect (name: sql fragment for ADD COLUMN)
            required = {
                'entry_cam': 'INTEGER',
                'exit_cam': 'INTEGER',
                'paid_amount': 'INTEGER DEFAULT 0',
                'created_at': "TEXT DEFAULT CURRENT_TIMESTAMP",
                'status': "TEXT DEFAULT 'IN'"
            }

            for name, definition in required.items():
                if name not in existing:
                    try:
                        conn.execute(f"ALTER TABLE sessions ADD COLUMN {name} {definition}")
                    except Exception:
                        # best-effort migration; ignore failures
                        pass
        except Exception:
            pass
    print("[OK] Database initialized")


def start_parking(plate: str, entry_cam: int = 0) -> Tuple[bool, str]:
    """
    Record vehicle entry.
    
    Args:
        plate: License plate text.
        entry_cam: Camera ID (default 0).
        
    Returns:
        (success: bool, message: str)
    """
    try:
        with get_db() as conn:
            # Check if plate already has an open session
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM sessions WHERE plate = ? AND status = 'IN'",
                (plate,)
            )
            if cur.fetchone():
                return False, f"[WARNING] Plate {plate} already IN parking lot"
            
            # Insert new entry
            now = datetime.now().isoformat(timespec='seconds')
            conn.execute(
                "INSERT INTO sessions (plate, entry_time, status, entry_cam) VALUES (?, ?, ?, ?)",
                (plate, now, 'IN', entry_cam)
            )
            return True, f"[OK] Entry recorded: {plate} @ {now}"
    except Exception as e:
        return False, f"❌ Database error: {e}"


def end_parking(plate: str, amount: int, exit_cam: int = 1) -> Tuple[bool, str]:
    """
    Record vehicle exit and payment.
    
    Args:
        plate: License plate text.
        amount: Payment amount in rupees.
        exit_cam: Camera ID (default 1).
        
    Returns:
        (success: bool, message: str)
    """
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Find latest open session for this plate
            cur.execute(
                "SELECT id FROM sessions WHERE plate = ? AND status = 'IN' ORDER BY id DESC LIMIT 1",
                (plate,)
            )
            row = cur.fetchone()
            if not row:
                return False, f"[ERROR] No open session found for {plate}"
            
            session_id = row[0]
            now = datetime.now().isoformat(timespec='seconds')
            
            # Update session with exit details
            conn.execute(
                "UPDATE sessions SET exit_time = ?, paid_amount = ?, status = 'OUT', exit_cam = ? WHERE id = ?",
                (now, amount, exit_cam, session_id)
            )
            return True, f"[OK] Exit recorded: {plate} @ {now}, Payment: Rs {amount}"
    except Exception as e:
        return False, f"❌ Database error: {e}"


def get_active_sessions() -> List[Dict]:
    """Get all currently parked vehicles."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, plate, entry_time FROM sessions WHERE status = 'IN' ORDER BY entry_time DESC"
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def get_recent_exits(limit: int = 20) -> List[Dict]:
    """Get recent exit records."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, plate, entry_time, exit_time, paid_amount FROM sessions WHERE status = 'OUT' ORDER BY exit_time DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def get_revenue() -> int:
    """Get total revenue from all exits."""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT SUM(paid_amount) FROM sessions WHERE status = 'OUT'")
            result = cur.fetchone()[0]
            return result or 0
    except Exception:
        return 0