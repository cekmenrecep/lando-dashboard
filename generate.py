#!/usr/bin/env python3
"""Generate Polymarket Paper Trading Dashboard HTML from portfolio command output"""
import json, os, subprocess, datetime, re

PORTFOLIO_PATH = os.path.expanduser("~/.polymarket/portfolio.json")
OUTPUT_PATH = "/data/.openclaw/workspace/dashboard/index.html"
SCRIPT = "/data/.openclaw/workspace/skills/polymarketodds/scripts/polymarket.py"

# Read raw portfolio for history
with open(PORTFOLIO_PATH) as f:
    portfolio = json.load(f)

positions = portfolio.get("positions", [])
history = portfolio.get("history", [])
cash = portfolio.get("cash", 0)

# Get live data from portfolio command
r = subprocess.run(["python3", SCRIPT, "portfolio"], capture_output=True, text=True, timeout=60)
portfolio_output = r.stdout

# Parse portfolio output
live_data = []
total_value = 0
total_cost = 0

for pos in positions:
    name = pos.get("outcome") or pos.get("name") or ""
    entry = pos["entry_price"]
    cost = pos["cost_basis"]
    shares = pos["shares"]
    
    # Find current price from portfolio output
    current_price = entry  # fallback
    for line in portfolio_output.split("\n"):
        if name in line and "→" in line:
            match = re.search(r'→\s*(\d+\.?\d*)%', line)
            if match:
                current_price = float(match.group(1)) / 100
                break
    
    value = shares * current_price
    pnl = value - cost
    pnl_pct = (pnl / cost * 100) if cost > 0 else 0
    
    live_data.append({
        "name": name,
        "slug": pos["slug"],
        "shares": shares,
        "entry_price": entry,
        "current_price": current_price,
        "cost": cost,
        "value": round(value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "bought_at": pos.get("bought_at", "")
    })
    total_value += value
    total_cost += cost

total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
portfolio_total = cash + total_value

# Categorize
safe = [p for p in live_data if p["entry_price"] >= 0.5]
yolo = [p for p in live_data if 0.05 <= p["entry_price"] < 0.5]
moonshot = [p for p in live_data if p["entry_price"] < 0.05]

# Sort each by value desc
safe.sort(key=lambda x: x["value"], reverse=True)
yolo.sort(key=lambda x: x["value"], reverse=True)
moonshot.sort(key=lambda x: x["value"], reverse=True)

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# Target
TARGET = 180000
progress = min(portfolio_total / TARGET * 100, 100)

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>🎰 Lando's Trading Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ 
    background: #0a0a0f; color: #e0e0e0; font-family: 'SF Pro', -apple-system, sans-serif;
    padding: 16px; min-height: 100vh;
}}
.header {{ text-align: center; padding: 20px 0; }}
.header h1 {{ font-size: 1.8em; background: linear-gradient(135deg, #00d4aa, #7c4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.header .subtitle {{ color: #888; margin-top: 6px; font-size: 0.85em; }}
.target {{ text-align: center; margin: 10px 0; padding: 12px; background: #14141f; border-radius: 12px; border: 1px solid #222; }}
.target .goal {{ font-size: 0.8em; color: #7c4dff; }}
.target .car {{ font-size: 1.4em; }}
.stats-row {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 16px 0; }}
@media(min-width: 600px) {{ .stats-row {{ grid-template-columns: repeat(4, 1fr); }} }}
.stat-card {{ background: #14141f; border-radius: 12px; padding: 14px; border: 1px solid #222; }}
.stat-card .label {{ color: #888; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; }}
.stat-card .value {{ font-size: 1.5em; font-weight: 700; margin-top: 4px; }}
.stat-card .value.green {{ color: #00d4aa; }}
.stat-card .value.red {{ color: #ff4757; }}
.stat-card .value.neutral {{ color: #e0e0e0; }}
.section {{ margin: 24px 0; }}
.section h2 {{ font-size: 1.1em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
.section h2 .badge {{ background: #222; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; color: #888; }}
.position {{ background: #14141f; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; border: 1px solid #222; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
.position:hover {{ border-color: #444; }}
.position .left {{ flex: 1; min-width: 180px; }}
.position .name {{ font-weight: 600; font-size: 0.95em; }}
.position .meta {{ color: #666; font-size: 0.75em; margin-top: 3px; }}
.position .right {{ text-align: right; }}
.position .pnl {{ font-size: 1.05em; font-weight: 700; }}
.position .pnl.green {{ color: #00d4aa; }}
.position .pnl.red {{ color: #ff4757; }}
.position .details {{ color: #888; font-size: 0.75em; margin-top: 3px; }}
.risk-tag {{ display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 0.65em; font-weight: 600; margin-left: 6px; }}
.risk-safe {{ background: #00d4aa22; color: #00d4aa; }}
.risk-yolo {{ background: #ffa50022; color: #ffa500; }}
.risk-moon {{ background: #7c4dff22; color: #7c4dff; }}
.progress-bar {{ width: 100%; height: 8px; background: #222; border-radius: 4px; margin-top: 10px; overflow: hidden; }}
.progress-fill {{ height: 100%; border-radius: 4px; }}
.history {{ margin-top: 24px; }}
.history h2 {{ margin-bottom: 12px; }}
.trade {{ display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #1a1a2a; font-size: 0.8em; }}
.trade .buy {{ color: #00d4aa; }}
.trade .sell {{ color: #ff4757; }}
.footer {{ text-align: center; padding: 24px 0; color: #444; font-size: 0.75em; }}
</style>
</head>
<body>

<div class="header">
    <h1>🎰 Lando's Paper Trading</h1>
    <div class="subtitle">Polymarket • {now}</div>
</div>

<div class="target">
    <div class="car">🚗 G-Wagon Challenge</div>
    <div class="goal">${portfolio_total:,.0f} / $180,000 ({progress:.2f}%)</div>
    <div class="progress-bar">
        <div class="progress-fill" style="width: {progress:.1f}%; background: linear-gradient(90deg, #00d4aa, #7c4dff);"></div>
    </div>
</div>

<div class="stats-row">
    <div class="stat-card">
        <div class="label">💰 Portföy</div>
        <div class="value neutral">${portfolio_total:,.2f}</div>
    </div>
    <div class="stat-card">
        <div class="label">📊 Yatırılan</div>
        <div class="value neutral">${total_cost:,.2f}</div>
    </div>
    <div class="stat-card">
        <div class="label">📈 P&L</div>
        <div class="value {'green' if total_pnl >= 0 else 'red'}">${'+' if total_pnl >= 0 else ''}{total_pnl:,.2f}</div>
    </div>
    <div class="stat-card">
        <div class="label">💵 Nakit</div>
        <div class="value neutral">${cash:,.2f}</div>
    </div>
</div>

<div style="text-align:center; color:#666; font-size:0.75em; margin:4px 0;">
    {len(live_data)} pozisyon • {len(safe)} güvenli • {len(yolo)} YOLO • {len(moonshot)} moonshot
</div>
"""

def render_positions(positions, emoji, title, risk_class):
    if not positions:
        return ""
    total_sect = sum(p["value"] for p in positions)
    h = f'<div class="section"><h2>{emoji} {title} <span class="badge">{len(positions)} pos • ${total_sect:,.0f}</span></h2>'
    for p in positions:
        pnl_class = "green" if p["pnl"] >= 0 else "red"
        pnl_sign = "+" if p["pnl"] >= 0 else ""
        tag_label = "🛡️ Safe" if risk_class == "safe" else "🎲 YOLO" if risk_class == "yolo" else "🌙 Moon"
        risk_tag = f'<span class="risk-tag risk-{risk_class}">{tag_label}</span>'
        potential = ""
        if risk_class in ("yolo", "moon") and p["entry_price"] > 0:
            mult = 1.0 / p["entry_price"]
            potential = f' • {mult:.0f}x potential'
        h += f'''<div class="position">
    <div class="left">
        <div class="name">{p["name"]}{risk_tag}</div>
        <div class="meta">{p["shares"]:.0f} shares @ {p["entry_price"]*100:.1f}% → {p["current_price"]*100:.1f}%{potential}</div>
    </div>
    <div class="right">
        <div class="pnl {pnl_class}">{pnl_sign}${p["pnl"]:.2f} ({pnl_sign}{p["pnl_pct"]:.1f}%)</div>
        <div class="details">${p["cost"]:.0f} → ${p["value"]:.2f}</div>
    </div>
</div>'''
    h += '</div>'
    return h

html += render_positions(safe, "🛡️", "Güvenli", "safe")
html += render_positions(yolo, "🎲", "YOLO", "yolo")
html += render_positions(moonshot, "🌙", "Moonshot", "moon")

# Trade history (last 15)
html += '<div class="history"><h2>📜 Son Trade\'ler</h2>'
for trade in reversed(history[-15:]):
    action_class = "buy" if trade["action"] == "buy" else "sell"
    action_text = "ALIŞ" if trade["action"] == "buy" else "SATIŞ"
    time_str = trade.get("at", "")[:16].replace("T", " ")
    html += f'''<div class="trade">
    <span class="{action_class}">{action_text}</span>
    <span>{trade.get("outcome", trade.get("slug", ""))}</span>
    <span>${trade["amount"]:.0f} @ {trade["price"]*100:.1f}%</span>
    <span style="color:#666">{time_str}</span>
</div>'''

html += f'''</div>
<div class="footer">
    🎰 Lando Paper Trading • OpenClaw + Polymarket<br>
    Hedef: G-Wagon ($180K) 🚗 • Otomatik güncelleme: 30dk
</div>
</body></html>'''

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write(html)

print(f"Dashboard generated: {OUTPUT_PATH}")
