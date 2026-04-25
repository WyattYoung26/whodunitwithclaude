"""
seed.py — Populates usage.db with realistic fake data for demo purposes.
Run from the src folder: python3 seed.py
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "usage.db"

USERS = [
    ("u_001", "Sarah K."),
    ("u_002", "Marcus T."),
    ("u_003", "Priya R."),
    ("u_004", "James L."),
    ("u_005", "Aisha M."),
    ("u_006", "Tyler B."),
    ("u_007", "Keiko S."),
]

MODELS = ["claude-opus-4-6", "claude-sonnet-4-6"]

# How active each user is (calls per day, rough average)
ACTIVITY = {
    "u_001": 18,
    "u_002": 14,
    "u_003": 11,
    "u_004": 9,
    "u_005": 7,
    "u_006": 5,
    "u_007": 4,
}

def seed(days_back: int = 30):
    con = sqlite3.connect(DB_PATH)

    # Make sure tables exist
    con.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       TEXT    NOT NULL,
            user_name     TEXT    NOT NULL,
            timestamp     TEXT    NOT NULL,
            input_tokens  INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            model         TEXT    NOT NULL,
            duration_ms   INTEGER
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_activity (
            user_id TEXT NOT NULL,
            date    TEXT NOT NULL,
            PRIMARY KEY (user_id, date)
        )
    """)

    rows = 0
    for day_offset in range(days_back, -1, -1):
        day = datetime.utcnow() - timedelta(days=day_offset)

        for user_id, user_name in USERS:
            # Skip some days randomly to create realistic gaps
            if random.random() < 0.15:
                continue

            calls_today = max(1, int(random.gauss(ACTIVITY[user_id], 3)))
            for _ in range(calls_today):
                hour   = random.randint(7, 19)
                minute = random.randint(0, 59)
                ts     = day.replace(hour=hour, minute=minute, second=random.randint(0,59))

                input_tokens  = random.randint(200, 4000)
                output_tokens = random.randint(100, 2000)
                model         = random.choice(MODELS)
                duration_ms   = random.randint(400, 3000)

                con.execute(
                    "INSERT INTO token_usage (user_id, user_name, timestamp, input_tokens, output_tokens, model, duration_ms) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, user_name, ts.isoformat(), input_tokens, output_tokens, model, duration_ms)
                )
                con.execute(
                    "INSERT OR IGNORE INTO daily_activity (user_id, date) VALUES (?, ?)",
                    (user_id, day.date().isoformat())
                )
                rows += 1

    con.commit()
    con.close()
    print(f"Seeded {rows} rows across {len(USERS)} users over {days_back} days ✓")

if __name__ == "__main__":
    seed()