import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "askse.db"

def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS faqs (
            faq_id INTEGER PRIMARY KEY AUTOINCREMENT,
            faq_code TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(category_id)
        );

        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'English',
            citations TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                ON DELETE CASCADE
        );
        """)
        for category in ["Labs", "Academics", "Library", "Exams", "Fees", "FYP", "Transport", "Help", "General"]:
            conn.execute(
                "INSERT OR IGNORE INTO categories(category_name) VALUES (?)",
                (category,)
            )

def create_conversation():
    timestamp = now_utc()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO conversations(created_at, updated_at) VALUES (?, ?)",
            (timestamp, timestamp)
        )
        return cur.lastrowid

def save_message(conversation_id, role, content, language="English", citations=None):
    import json
    timestamp = now_utc()
    citations_json = json.dumps(citations or [])
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO messages
               (conversation_id, role, content, language, citations, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conversation_id, role, content, language, citations_json, timestamp)
        )
        conn.execute(
            "UPDATE conversations SET updated_at=? WHERE conversation_id=?",
            (timestamp, conversation_id)
        )

def get_history(conversation_id):
    import json
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT message_id, role, content, language, citations, created_at
               FROM messages WHERE conversation_id=?
               ORDER BY message_id ASC""",
            (conversation_id,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["citations"] = json.loads(item["citations"])
        result.append(item)
    return result

def clear_conversation(conversation_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM conversations WHERE conversation_id=?",
            (conversation_id,)
        )

def list_faqs(active_only=True):
    query = """SELECT f.faq_code, f.question, f.answer, f.is_active,
                      c.category_name AS category, f.created_at
               FROM faqs f JOIN categories c ON c.category_id=f.category_id"""
    if active_only:
        query += " WHERE f.is_active=1"
    query += " ORDER BY f.faq_id"
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query).fetchall()]

def insert_faq(question, answer, category):
    question = question.strip()
    answer = answer.strip()
    category = category.strip() or "General"
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO categories(category_name) VALUES (?)",
            (category,)
        )
        category_id = conn.execute(
            "SELECT category_id FROM categories WHERE category_name=?",
            (category,)
        ).fetchone()["category_id"]
        next_id = conn.execute(
            "SELECT COALESCE(MAX(faq_id), 0) + 1 AS next_id FROM faqs"
        ).fetchone()["next_id"]
        faq_code = f"FAQ-{next_id:02d}"
        conn.execute(
            """INSERT INTO faqs
               (faq_code, category_id, question, answer, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (faq_code, category_id, question, answer, now_utc())
        )
        return faq_code
