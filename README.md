# tokenboard

A lightweight leaderboard that tracks Claude API token usage per user and turns it into a competitive dashboard. Drop it into any Python codebase in minutes.

![Python](https://img.shields.io/badge/python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green) ![SQLite](https://img.shields.io/badge/storage-SQLite-lightgrey)

---

## Features

- **One-line integration** — swap your existing Anthropic client for `TrackedClient`, nothing else changes
- **Live leaderboard** — ranked by total tokens, updates every 30 seconds
- **Automatic badges** — Champion, On a streak, Volume king, Speed runner
- **Streak tracking** — consecutive days of activity per user
- **Weekly sparklines** — 7-day usage trends for top users
- **Three time periods** — this week, this month, all time

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
git clone https://github.com/your-org/tokenboard.git
cd tokenboard
pip install anthropic fastapi uvicorn python-dotenv
```

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

> **Never commit your `.env` file.** It's already in `.gitignore`.

## Usage

Replace your existing Anthropic client with `TrackedClient`:

```python
# Before
import anthropic
client = anthropic.Anthropic()

# After — one line change, everything else stays the same
from tracker import TrackedClient
client = TrackedClient(user_id="u_001", user_name="Sarah K.")

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Each user in your team gets their own `TrackedClient` instance. Token usage is logged to a local SQLite database automatically after every API call.

## Running the dashboard

```bash
uvicorn server:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project structure

```
tokenboard/
├── tracker.py        # Drop-in Anthropic client wrapper
├── stats.py          # Leaderboard queries (rankings, streaks, badges)
├── server.py         # FastAPI server + dashboard UI
├── example_usage.py  # Integration example
├── .env              # Your API key — never committed
├── .gitignore
└── README.md
```

> `usage.db` is created automatically on first run and is excluded from version control — it contains real user data.

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/leaderboard?period=month` | Ranked users (`week` / `month` / `all`) |
| `GET /api/summary` | Team-wide totals for the past 30 days |
| `GET /api/sparklines` | 7-day daily token breakdown for top users |

## Badges

| Badge | Awarded when |
|-------|-------------|
| 🏆 Champion | Rank #1 for the selected period |
| 🔥 On a streak | 7+ consecutive active days |
| 💼 Volume king | 500K+ tokens in the period |
| ⚡ Speed runner | Average API response under 800ms |

## Deployment

The easiest zero-config options with free tiers:

- [Railway](https://railway.app) — connect your repo, set `ANTHROPIC_API_KEY` as an env var, deploy
- [Render](https://render.com) — same flow, also free tier
- [Fly.io](https://fly.io) — more control, still straightforward

For teams with multiple servers writing simultaneously, swap SQLite for PostgreSQL by updating the connection string in `tracker.py` and `stats.py`.

## Security notes

- API keys are loaded from environment variables, never hardcoded
- `usage.db` and `.env` are gitignored by default
- The dashboard has no authentication out of the box — add it before exposing to the internet

## License

MIT