#!/usr/bin/env python3
"""Generate Polymarket Paper Trading Dashboard HTML - parses portfolio command directly"""
import json, os, subprocess, datetime, re

PORTFOLIO_PATH = os.path.expanduser("~/.polymarket/portfolio.json")
OUTPUT_PATH = "/data/.openclaw/workspace/dashboard/index.html"
SCRIPT = "/data/.openclaw/workspace/skills/polymarketodds/scripts/polymarket.py"

with open(PORTFOLIO_PATH) as f:
    portfolio = json.load(f)

history = portfolio.get("history", [])
cash = portfolio.get("cash", 0)

# Parse portfolio command output directly
r = subprocess.run(["python3", SCRIPT, "portfolio"], capture_output=True, text=True, timeout=60)
output = r.stdout

# Parse positions from output
live_data = []
total_value = 0
total_cost = 0
total_pnl = 0

lines = output.split("\n")
i = 0
while i < len(lines):
    line = lines[i]
    # Look for position name lines (bold markers)
    if line.strip().startswith("🟢") or line.strip().startswith("🔴"):
        name = line.strip().replace("🟢", "").replace("🔴", "").replace("**", "").strip()
        
        # Next line has shares info
        entry_price = 0
        current_price = 0
        shares = 0
        value = 0
        pnl_val = 0
        pnl_pct = 0
        cost = 0
        
        if i+1 < len(lines):
            info_line = lines[i+1].strip()
            # "313 shares @ 95.9% → 95.9%"
            m = re.search(r'(\d+)\s+shares\s+@\s+(\d+\.?\d*)%\s+→\s+(\d+\.?\d*)%', info_line)
            if m:
                shares = int(m.group(1))
                entry_price = float(m.group(2)) / 100
                current_price = float(m.group(3)) / 100
        
        if i+2 < len(lines):
            val_line = lines[i+2].strip()
            # "Value: $300.00 | P&L: $+0.00 (+0.0%)"
            vm = re.search(r'Value:\s*\$([0-9,]+\.?\d*)', val_line)
            pm = re.search(r'P&L:\s*\$([+-]?[0-9,]+\.?\d*)\s+\(([+-]?\d+\.?\d*)%\)', val_line)
            if vm:
                value = float(vm.group(1).replace(",", ""))
            if pm:
                pnl_val = float(pm.group(1).replace(",", ""))
                pnl_pct = float(pm.group(2))
        
        cost = value - pnl_val
        total_value += value
        total_cost += cost
        total_pnl += pnl_val
        
        live_data.append({
            "name": name,
            "shares": shares,
            "entry_price": entry_price,
            "current_price": current_price,
            "cost": round(cost, 2),
            "value": round(value, 2),
            "pnl": round(pnl_val, 2),
            "pnl_pct": round(pnl_pct, 2),
        })
        i += 3
        continue
    i += 1

total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
portfolio_total = cash + total_value

# Categorize
safe = [p for p in live_data if p["entry_price"] >= 0.5]
yolo = [p for p in live_data if 0.05 <= p["entry_price"] < 0.5]
moonshot = [p for p in live_data if p["entry_price"] < 0.05]

safe.sort(key=lambda x: x["value"], reverse=True)
yolo.sort(key=lambda x: x["value"], reverse=True)
moonshot.sort(key=lambda x: x["value"], reverse=True)

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
TARGET = 180000
progress = min(portfolio_total / TARGET * 100, 100)

pnl_color = "green" if total_pnl >= 0 else "red"
pnl_sign = "+" if total_pnl >= 0 else ""

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>🎰 Lando's Trading Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0f; color: #e0e0e0; font-family: -apple-system, sans-serif; padding: 16px; min-height: 100vh; }}
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
.green {{ color: #00d4aa; }}
.red {{ color: #ff4757; }}
.neutral {{ color: #e0e0e0; }}
.section {{ margin: 24px 0; }}
.section h2 {{ font-size: 1.1em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
.badge {{ background: #222; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; color: #888; }}
.position {{ background: #14141f; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; border: 1px solid #222; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
.position:hover {{ border-color: #444; }}
.position .left {{ flex: 1; min-width: 180px; }}
.position .name {{ font-weight: 600; font-size: 0.95em; }}
.position .meta {{ color: #666; font-size: 0.75em; margin-top: 3px; }}
.position .right {{ text-align: right; }}
.position .pnl {{ font-size: 1.05em; font-weight: 700; }}
.position .details {{ color: #888; font-size: 0.75em; margin-top: 3px; }}
.risk-tag {{ display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 0.65em; font-weight: 600; margin-left: 6px; }}
.risk-safe {{ background: #00d4aa22; color: #00d4aa; }}
.risk-yolo {{ background: #ffa50022; color: #ffa500; }}
.risk-moon {{ background: #7c4dff22; color: #7c4dff; }}
.progress-bar {{ width: 100%; height: 8px; background: #222; border-radius: 4px; margin-top: 10px; overflow: hidden; }}
.progress-fill {{ height: 100%; border-radius: 4px; }}
.history {{ margin-top: 24px; }}
.trade {{ display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #1a1a2a; font-size: 0.8em; }}
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
    <div class="progress-bar"><div class="progress-fill" style="width: {progress:.1f}%; background: linear-gradient(90deg, #00d4aa, #7c4dff);"></div></div>
</div>
<div class="stats-row">
    <div class="stat-card"><div class="label">💰 Portföy</div><div class="value neutral">${portfolio_total:,.2f}</div></div>
    <div class="stat-card"><div class="label">📊 Yatırılan</div><div class="value neutral">${total_cost:,.2f}</div></div>
    <div class="stat-card"><div class="label">📈 P&L</div><div class="value {pnl_color}">{pnl_sign}${total_pnl:,.2f} ({pnl_sign}{total_pnl_pct:.1f}%)</div></div>
    <div class="stat-card"><div class="label">💵 Nakit</div><div class="value neutral">${cash:,.2f}</div></div>
</div>
<div style="text-align:center; color:#666; font-size:0.75em; margin:4px 0;">
    {len(live_data)} pozisyon • {len(safe)} güvenli • {len(yolo)} YOLO • {len(moonshot)} moonshot
</div>
"""

def render_positions(positions, emoji, title, risk_class):
    if not positions: return ""
    total_s = sum(p["value"] for p in positions)
    h = f'<div class="section"><h2>{emoji} {title} <span class="badge">{len(positions)} pos • ${total_s:,.0f}</span></h2>'
    for p in positions:
        pc = "green" if p["pnl"] >= 0 else "red"
        ps = "+" if p["pnl"] >= 0 else ""
        tag = "🛡️ Safe" if risk_class == "safe" else "🎲 YOLO" if risk_class == "yolo" else "🌙 Moon"
        pot = ""
        if risk_class in ("yolo","moon") and p["entry_price"] > 0:
            pot = f' • {1/p["entry_price"]:.0f}x pot.'
        h += f'''<div class="position">
<div class="left"><div class="name">{p["name"]}<span class="risk-tag risk-{risk_class}">{tag}</span></div>
<div class="meta">{p["shares"]:.0f} sh @ {p["entry_price"]*100:.1f}% → {p["current_price"]*100:.1f}%{pot}</div></div>
<div class="right"><div class="pnl {pc}">{ps}${p["pnl"]:.2f} ({ps}{p["pnl_pct"]:.1f}%)</div>
<div class="details">${p["cost"]:.0f} → ${p["value"]:.2f}</div></div></div>'''
    h += '</div>'
    return h

html += render_positions(safe, "🛡️", "Güvenli", "safe")
html += render_positions(yolo, "🎲", "YOLO", "yolo")
html += render_positions(moonshot, "🌙", "Moonshot", "moon")

html += '<div class="history"><h2>📜 Son Trade\'ler</h2>'
for t in reversed(history[-15:]):
    ac = "green" if t["action"]=="buy" else "red"
    at = "ALIŞ" if t["action"]=="buy" else "SATIŞ"
    ts = t.get("at","")[:16].replace("T"," ")
    html += f'<div class="trade"><span class="{ac}">{at}</span><span>{t.get("outcome",t.get("slug",""))}</span><span>${t["amount"]:.0f} @ {t["price"]*100:.1f}%</span><span style="color:#666">{ts}</span></div>'

html += f'</div><div class="footer">🎰 Lando Paper Trading • OpenClaw + Polymarket<br>Hedef: G-Wagon ($180K) 🚗 • Auto-refresh: 30dk</div></body></html>'

with open(OUTPUT_PATH, "w") as f:
    f.write(html)
print(f"Dashboard generated - {len(live_data)} positions, P&L: ${total_pnl:+.2f}")
