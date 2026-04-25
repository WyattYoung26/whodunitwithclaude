"""
tracker.py — Drop-in Claude API wrapper that logs token usage to SQLite.
Usage: replace your `anthropic.Anthropic()` client with `TrackedClient()`.
"""

import sqlite3
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
import anthropic

from dotenv import load_dotenv
load_dotenv()  # Load ANTHROPIC_API_KEY from .env file

DB_PATH = Path(__file__).parent / "usage.db"


def init_db():
    """Create the database and tables if they don't exist."""
    con = sqlite3.connect(DB_PATH)
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
    # Streak tracking helper — one row per user per calendar day
    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_activity (
            user_id TEXT NOT NULL,
            date    TEXT NOT NULL,
            PRIMARY KEY (user_id, date)
        )
    """)
    con.commit()
    con.close()


def log_usage(user_id: str, user_name: str, input_tokens: int,
              output_tokens: int, model: str, duration_ms: int = None):
    """Write one API call's token usage to the database."""
    now = datetime.utcnow().isoformat()
    today = datetime.utcnow().date().isoformat()
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO token_usage (user_id, user_name, timestamp, input_tokens, output_tokens, model, duration_ms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, user_name, now, input_tokens, output_tokens, model, duration_ms)
    )
    # Upsert daily activity for streak tracking
    con.execute(
        "INSERT OR IGNORE INTO daily_activity (user_id, date) VALUES (?, ?)",
        (user_id, today)
    )
    con.commit()
    con.close()


class TrackedClient:
    """
    Wraps the Anthropic client. Use exactly like `anthropic.Anthropic()`,
    but pass user_id and user_name so usage gets attributed correctly.

    Example:
        client = TrackedClient(user_id="u_001", user_name="Sarah K.")
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """

    def __init__(self, user_id: str, user_name: str, **anthropic_kwargs):
        self.user_id = user_id
        self.user_name = user_name
        self._client = anthropic.Anthropic(**anthropic_kwargs)
        self.messages = _TrackedMessages(self._client, user_id, user_name)


class _TrackedMessages:
    def __init__(self, client, user_id, user_name):
        self._client = client
        self.user_id = user_id
        self.user_name = user_name

    def create(self, **kwargs):
        t0 = time.monotonic()
        response = self._client.messages.create(**kwargs)
        duration_ms = int((time.monotonic() - t0) * 1000)

        log_usage(
            user_id=self.user_id,
            user_name=self.user_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
            duration_ms=duration_ms,
        )
        return response


# --- Initialize DB on import ---
init_db()