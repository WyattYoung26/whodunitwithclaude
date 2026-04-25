"""
stats.py — Query functions that power the leaderboard dashboard.
All functions return plain dicts/lists — easy to serve via any web framework.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "usage.db"


def _con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def leaderboard(period: str = "month"):
    """
    Return ranked users by total tokens for the given period.
    period: 'week' | 'month' | 'all'
    """
    cutoff = {
        "week":  (date.today() - timedelta(days=7)).isoformat(),
        "month": (date.today() - timedelta(days=30)).isoformat(),
        "all":   "2000-01-01",
    }.get(period, "2000-01-01")

    con = _con()
    rows = con.execute("""
        SELECT
            user_id,
            user_name,
            SUM(input_tokens + output_tokens)  AS total_tokens,
            SUM(input_tokens)                  AS input_tokens,
            SUM(output_tokens)                 AS output_tokens,
            COUNT(*)                           AS api_calls,
            AVG(duration_ms)                   AS avg_duration_ms
        FROM token_usage
        WHERE timestamp >= ?
        GROUP BY user_id, user_name
        ORDER BY total_tokens DESC
    """, (cutoff,)).fetchall()
    con.close()

    result = []
    for rank, row in enumerate(rows, start=1):
        result.append({
            "rank":           rank,
            "user_id":        row["user_id"],
            "user_name":      row["user_name"],
            "total_tokens":   row["total_tokens"],
            "input_tokens":   row["input_tokens"],
            "output_tokens":  row["output_tokens"],
            "api_calls":      row["api_calls"],
            "avg_duration_ms": round(row["avg_duration_ms"] or 0),
            "streak_days":    _streak(row["user_id"]),
            "badges":         _badges(row, rank),
        })
    return result


def team_summary():
    """High-level numbers for the summary cards at the top of the dashboard."""
    con = _con()
    row = con.execute("""
        SELECT
            SUM(input_tokens + output_tokens) AS total_tokens,
            COUNT(DISTINCT user_id)           AS user_count,
            COUNT(*)                          AS total_calls
        FROM token_usage
        WHERE timestamp >= date('now', '-30 days')
    """).fetchone()
    con.close()
    return {
        "total_tokens": row["total_tokens"] or 0,
        "user_count":   row["user_count"] or 0,
        "total_calls":  row["total_calls"] or 0,
    }


def weekly_sparklines(top_n: int = 5):
    """
    Return 7-day daily token totals per user (for trend sparklines).
    Only includes the top N users by 30-day volume.
    """
    con = _con()
    top_users = con.execute("""
        SELECT user_id, user_name
        FROM token_usage
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY user_id
        ORDER BY SUM(input_tokens + output_tokens) DESC
        LIMIT ?
    """, (top_n,)).fetchall()

    result = []
    for user in top_users:
        days = []
        for i in range(6, -1, -1):          # 6 days ago → today
            day = (date.today() - timedelta(days=i)).isoformat()
            row = con.execute("""
                SELECT COALESCE(SUM(input_tokens + output_tokens), 0) AS tokens
                FROM token_usage
                WHERE user_id = ? AND DATE(timestamp) = ?
            """, (user["user_id"], day)).fetchone()
            days.append({"date": day, "tokens": row["tokens"]})
        result.append({"user_id": user["user_id"], "user_name": user["user_name"], "days": days})
    con.close()
    return result


def _streak(user_id: str) -> int:
    """Count how many consecutive days (ending today) the user has been active."""
    con = _con()
    dates = {row[0] for row in con.execute(
        "SELECT date FROM daily_activity WHERE user_id = ?", (user_id,)
    ).fetchall()}
    con.close()

    streak = 0
    day = date.today()
    while day.isoformat() in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def _badges(row, rank: int) -> list[str]:
    badges = []
    if rank == 1:
        badges.append("champion")
    if _streak(row["user_id"]) >= 7:
        badges.append("on_a_streak")
    if row["total_tokens"] > 500_000:
        badges.append("volume_king")
    if (row["avg_duration_ms"] or 9999) < 800:
        badges.append("speed_runner")
    return badges