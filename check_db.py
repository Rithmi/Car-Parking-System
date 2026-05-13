import sqlite3

conn = sqlite3.connect("parking.db")
cursor = conn.cursor()

print("📋 Tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

print("\n📊 Last 5 parking records:")
try:
    cursor.execute("SELECT * FROM parking_records ORDER BY id DESC LIMIT 5;")
    rows = cursor.fetchall()
    if not rows:
        print("❌ No records found")
    else:
        for r in rows:
            print(r)
except Exception as e:
    print("❌ Error reading parking_records:", e)

conn.close()
