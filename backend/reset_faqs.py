
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "askse.db"

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)

try:
    count = conn.execute(
        "SELECT COUNT(*) FROM faqs"
    ).fetchone()[0]

    conn.execute("DELETE FROM faqs")
    conn.commit()

    print(f"Successfully removed {count} existing FAQs.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
