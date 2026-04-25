# whodunitwithclaude
Fun claude token usage dashboard you can put in your office to see who really gets their moneys worth.

# Claude Token Tracker

A lightweight leaderboard that tracks Claude API token usage per user and turns it into a competitive dashboard.

## Files

| File | What it does |
|------|-------------|
| `tracker.py` | Drop-in wrapper around the Anthropic client — logs every API call |
| `stats.py`   | Query functions: leaderboard, summary cards, sparklines |
| `server.py`  | FastAPI server — serves the live dashboard at localhost:8000 |
| `usage.db`   | SQLite database (auto-created on first run) |

## Setup

```bash
pip install anthropic fastapi uvicorn
```

Set your API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Integration (one line change)

```python
# Before
import anthropic
client = anthropic.Anthropic()

# After — just swap the client
from tracker import TrackedClient
client = TrackedClient(user_id="u_001", user_name="Sarah K.")

# All .messages.create() calls are identical
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Run the dashboard

```bash
uvicorn server:app --reload
# Open http://localhost:8000
```

The dashboard auto-refreshes every 30 seconds.

## API endpoints

- `GET /api/leaderboard?period=month` — ranked users (period: week/month/all)
- `GET /api/summary` — team-wide totals
- `GET /api/sparklines` — 7-day daily breakdown per top user

## Badges awarded automatically

| Badge | Condition |
|-------|-----------|
| Champion | Rank #1 this period |
| On a streak | 7+ consecutive active days |
| Volume king | 500K+ tokens this period |
| Speed runner | Avg API response under 800ms |

## Next steps

- Add authentication so only your team can see the dashboard
- Deploy to a server (Railway, Render, Fly.io are all free tiers)
- Swap SQLite for Postgres when you need multi-server writes
- Add cost tracking: `input_tokens * 0.000003 + output_tokens * 0.000015` (Sonnet pricing)


