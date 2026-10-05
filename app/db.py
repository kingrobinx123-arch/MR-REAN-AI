import os
import sqlite3
import time
from app.config import DATA_DIR, DB_PATH, DAILY_CREDITS

def _conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = _conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(
      telegram_id TEXT PRIMARY KEY,
      username TEXT DEFAULT '',
      blocked INTEGER DEFAULT 0,
      daily_credits INTEGER NOT NULL DEFAULT 20,
      used_today INTEGER NOT NULL DEFAULT 0,
      usage_day TEXT NOT NULL DEFAULT '',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS usage(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      telegram_id TEXT,
      provider TEXT,
      action TEXT,
      units INTEGER NOT NULL DEFAULT 1,
      created_at INTEGER NOT NULL
    );
    ''')
    c.commit()
    c.close()

def upsert_user(tid, username=""):
    tid = str(tid)
    now = int(time.time())
    c = _conn()
    row = c.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (tid,)).fetchone()
    if row:
        c.execute("UPDATE users SET username=?, updated_at=? WHERE telegram_id=?", (username, now, tid))
    else:
        c.execute(
            "INSERT INTO users(telegram_id,username,daily_credits,usage_day,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (tid, username, DAILY_CREDITS, time.strftime("%Y-%m-%d"), now, now)
        )
    c.commit()
    c.close()

def get_user(tid):
    tid = str(tid)
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)).fetchone()
    if row:
        day = time.strftime("%Y-%m-%d")
        if row["usage_day"] != day:
            c.execute("UPDATE users SET used_today=0, usage_day=?, updated_at=? WHERE telegram_id=?", (day, int(time.time()), tid))
            c.commit()
            row = c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)).fetchone()
    c.close()
    return row

def consume_credit(tid, provider, action):
    row = get_user(tid)
    if not row or row["blocked"] or row["used_today"] >= row["daily_credits"]:
        return False
    now = int(time.time())
    c = _conn()
    c.execute("UPDATE users SET used_today=used_today+1, updated_at=? WHERE telegram_id=?", (now, str(tid)))
    c.execute("INSERT INTO usage(telegram_id,provider,action,units,created_at) VALUES(?,?,?,?,?)",
              (str(tid), provider, action, 1, now))
    c.commit()
    c.close()
    return True

def list_users():
    c = _conn()
    rows = c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    c.close()
    return rows

def set_blocked(tid, value):
    c = _conn()
    c.execute("UPDATE users SET blocked=?, updated_at=? WHERE telegram_id=?", (int(bool(value)), int(time.time()), str(tid)))
    c.commit()
    c.close()

def set_credits(tid, credits):
    c = _conn()
    c.execute("UPDATE users SET daily_credits=?, updated_at=? WHERE telegram_id=?", (max(0, int(credits)), int(time.time()), str(tid)))
    c.commit()
    c.close()

def stats():
    c = _conn()
    users = c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
    blocked = c.execute("SELECT COUNT(*) n FROM users WHERE blocked=1").fetchone()["n"]
    used = c.execute("SELECT COALESCE(SUM(units),0) n FROM usage").fetchone()["n"]
    c.close()
    return {"users": users, "blocked": blocked, "usage": used}
