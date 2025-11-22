from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve()
DB_PATH = BASE_DIR.parent / "data" / "memory.sqlite"

print("DB path:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("\nTables:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())

print("\nmemories rows:")
cur.execute("SELECT * FROM memories;")
rows = cur.fetchall()
for r in rows:
    print(r)

conn.close()
