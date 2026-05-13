import sqlite3

conn = sqlite3.connect("parking.db")
cur = conn.cursor()

print("📌 sessions schema:")
cur.execute("PRAGMA table_info(sessions);")
for row in cur.fetchall():
    print(row)

print("\n📊 Last 10 rows in sessions:")
cur.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 10;")
rows = cur.fetchall()
if not rows:
    print("❌ sessions is empty (no entries recorded yet)")
else:
    for r in rows:
        print(r)

conn.close()
