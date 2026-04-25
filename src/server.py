"""
server.py — Minimal FastAPI server exposing the leaderboard data + a dashboard UI.
Run with:  uvicorn server:app --reload
Then open: http://localhost:8000
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import stats

app = FastAPI(title="Claude Token Tracker")


@app.get("/api/leaderboard")
def api_leaderboard(period: str = "month"):
    return stats.leaderboard(period)


@app.get("/api/summary")
def api_summary():
    return stats.team_summary()


@app.get("/api/sparklines")
def api_sparklines():
    return stats.weekly_sparklines()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the leaderboard dashboard as a single HTML page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Claude Token Leaderboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f5f2; color: #1a1a18; min-height: 100vh; }
  header { background: #fff; border-bottom: 1px solid #e0dfd6;
           padding: 1rem 2rem; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 18px; font-weight: 500; }
  .pill { background: #eeedfe; color: #3c3489; font-size: 11px;
          padding: 3px 10px; border-radius: 12px; font-weight: 500; }
  main { max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; }
  .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 2rem; }
  .metric { background: #fff; border: 1px solid #e0dfd6; border-radius: 10px;
            padding: 1rem 1.25rem; }
  .metric-label { font-size: 12px; color: #888780; margin-bottom: 4px; }
  .metric-value { font-size: 24px; font-weight: 500; }
  .board { background: #fff; border: 1px solid #e0dfd6; border-radius: 12px; overflow: hidden; }
  .board-header { display: grid; grid-template-columns: 44px 1fr 140px 90px;
                  padding: 10px 16px; border-bottom: 1px solid #e0dfd6;
                  background: #f9f9f7; font-size: 11px; color: #888780;
                  text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; }
  .board-header .r { text-align: right; }
  .row { display: grid; grid-template-columns: 44px 1fr 140px 90px;
         padding: 12px 16px; border-bottom: 1px solid #f0efe8;
         align-items: center; transition: background 0.1s; }
  .row:last-child { border-bottom: none; }
  .row:hover { background: #fafaf8; }
  .rank { font-size: 16px; text-align: center; }
  .user { display: flex; align-items: center; gap: 10px; }
  .avatar { width: 34px; height: 34px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center;
            font-size: 12px; font-weight: 500; flex-shrink: 0; }
  .name { font-size: 14px; font-weight: 500; }
  .badges { display: flex; gap: 4px; margin-top: 3px; flex-wrap: wrap; }
  .badge { font-size: 10px; padding: 1px 7px; border-radius: 10px; font-weight: 500; }
  .bar-wrap { display: flex; align-items: center; gap: 8px; }
  .bar-track { flex: 1; height: 6px; background: #f0efe8; border-radius: 3px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 3px; }
  .tokens { font-size: 13px; font-weight: 500; text-align: right; }
  .tabs { display: flex; gap: 6px; margin-bottom: 1rem; }
  .tab { padding: 6px 14px; border-radius: 8px; font-size: 13px; cursor: pointer;
         border: 1px solid #e0dfd6; background: transparent; color: #888780; }
  .tab.active { background: #fff; color: #1a1a18; font-weight: 500; }
</style>
</head>
<body>
<header>
  <h1>Claude Token Leaderboard</h1>
  <span class="pill">Live</span>
</header>
<main>
  <div class="metrics" id="metrics">
    <div class="metric"><div class="metric-label">Loading...</div></div>
  </div>
  <div class="tabs">
    <button class="tab active" onclick="load('month',this)">This month</button>
    <button class="tab" onclick="load('week',this)">This week</button>
    <button class="tab" onclick="load('all',this)">All time</button>
  </div>
  <div class="board">
    <div class="board-header">
      <span></span><span>User</span><span>Usage</span><span class="r">Tokens</span>
    </div>
    <div id="rows"></div>
  </div>
</main>

<script>
const AVATARS = ["#e6f1fb:#0c447c","#faeeda:#633806","#eaf3de:#27500a",
                 "#eeedfe:#3c3489","#faece7:#712b13","#e1f5ee:#085041"];
const BAR_COLORS = ["#c89b30","#888780","#9a5b2a","#378add","#1d9e75","#7f77dd","#d85a30"];
const RANK_ICONS = {1:"🥇",2:"🥈",3:"🥉"};
const BADGE_LABELS = {champion:"Champion",on_a_streak:"On a streak",
                      volume_king:"Volume king",speed_runner:"Speed runner"};
const BADGE_STYLES = {champion:"background:#faece7;color:#712b13",
                      on_a_streak:"background:#faeeda;color:#633806",
                      volume_king:"background:#eaf3de;color:#27500a",
                      speed_runner:"background:#e6f1fb;color:#0c447c"};

function fmt(n) {
  if (n >= 1_000_000) return (n/1_000_000).toFixed(2)+"M";
  if (n >= 1_000)     return Math.round(n/1_000)+"K";
  return n;
}
function initials(name) { return name.split(" ").map(w=>w[0]).join("").slice(0,2).toUpperCase(); }

async function load(period, btn) {
  document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");

  const [users, summary] = await Promise.all([
    fetch("/api/leaderboard?period="+period).then(r=>r.json()),
    fetch("/api/summary").then(r=>r.json()),
  ]);

  // Metrics
  const top = users[0];
  document.getElementById("metrics").innerHTML = `
    <div class="metric"><div class="metric-label">Total tokens (30d)</div>
      <div class="metric-value">${fmt(summary.total_tokens)}</div></div>
    <div class="metric"><div class="metric-label">Top performer</div>
      <div class="metric-value" style="font-size:18px">${top?.user_name||"—"}</div></div>
    <div class="metric"><div class="metric-label">Active users</div>
      <div class="metric-value">${summary.user_count}</div></div>
  `;

  const maxT = users[0]?.total_tokens || 1;
  document.getElementById("rows").innerHTML = users.map((u, i) => {
    const [bg, fg] = AVATARS[i % AVATARS.length].split(":");
    const pct = Math.round((u.total_tokens / maxT) * 100);
    const badgesHtml = u.badges.map(b =>
      `<span class="badge" style="${BADGE_STYLES[b]||""}">${BADGE_LABELS[b]||b}</span>`
    ).join("");
    return `
      <div class="row">
        <div class="rank">${RANK_ICONS[u.rank] || u.rank}</div>
        <div class="user">
          <div class="avatar" style="background:${bg};color:${fg}">${initials(u.user_name)}</div>
          <div>
            <div class="name">${u.user_name}</div>
            <div class="badges">${badgesHtml} ${u.streak_days>1?`<span class="badge" style="background:#faeeda;color:#633806">${u.streak_days}d streak</span>`:""}</div>
          </div>
        </div>
        <div class="bar-wrap">
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${BAR_COLORS[i%BAR_COLORS.length]}"></div></div>
          <span style="font-size:12px;color:#888780;min-width:36px;text-align:right">${pct}%</span>
        </div>
        <div class="tokens">${fmt(u.total_tokens)}</div>
      </div>`;
  }).join("");
}

load("month", document.querySelector(".tab"));
setInterval(() => load("month", document.querySelector(".tab.active")), 30000);
</script>
</body>
</html>"""