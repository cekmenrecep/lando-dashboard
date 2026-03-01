#!/usr/bin/env python3
"""Generate Polymarket Paper Trading Dashboard HTML"""
import json, os, subprocess, datetime, re

PORTFOLIO_PATH = os.path.expanduser("~/.polymarket/portfolio.json")
OUTPUT_PATH = "/data/.openclaw/workspace/dashboard/index.html"
SCRIPT = "/data/.openclaw/workspace/skills/polymarketodds/scripts/polymarket.py"

# Human-readable descriptions for each slug
SLUG_DESCRIPTIONS = {
    "fed-decision-in-march-885": "🏦 Fed Mart Toplantısı - Faiz Kararı",
    "who-will-trump-nominate-as-fed-chair": "🏛️ Trump'ın Fed Başkanı Adayı",
    "oscars-2026-best-picture-winner": "🎬 Oscar 2026 - En İyi Film",
    "what-will-happen-before-gta-vi": "🎮 GTA VI'dan Önce Ne Olacak?",
    "nba-mvp-694": "🏀 NBA MVP 2026",
    "us-x-russia-military-clash-by": "⚔️ ABD-Rusya Askeri Çatışma",
    "kraken-ipo-in-2025": "📈 Kraken Halka Arz (IPO)",
    "oscars-2026-best-actress-winner": "🎬 Oscar 2026 - En İyi Kadın Oyuncu",
    "oscars-2026-best-actor-winner": "🎬 Oscar 2026 - En İyi Erkek Oyuncu",
    "bitcoin-above-on-march-1": "₿ Bitcoin 1 Mart Fiyatı",
    "oscars-2026-best-supporting-actress-winner": "🎬 Oscar 2026 - En İyi Yardımcı Kadın Oyuncu",
    "nba-rookie-of-the-year-873": "🏀 NBA Yılın Çaylağı 2026",
    "2026-nba-champion": "🏀 2026 NBA Şampiyonu",
    "presidential-election-winner-2028": "🇺🇸 2028 ABD Başkanlık Seçimi",
    "2026-fifa-world-cup-winner-595": "⚽ 2026 FIFA Dünya Kupası Şampiyonu",
    "when-will-bitcoin-hit-150k": "₿ Bitcoin Ne Zaman $150K?",
    "oscars-2026-best-supporting-actor-winner": "🎬 Oscar 2026 - En İyi Yardımcı Erkek Oyuncu",
    "nba-eastern-conference-champion-442": "🏀 NBA Doğu Konferansı Şampiyonu",
    "will-the-iranian-regime-fall-by-the-end-of-2026": "🇮🇷 İran Rejimi 2027'den Önce Düşer mi?",
}

with open(PORTFOLIO_PATH) as f:
    portfolio = json.load(f)

history = portfolio.get("history", [])
cash = portfolio.get("cash", 0)
raw_positions = portfolio.get("positions", [])

# Build slug lookup from raw positions
slug_for_name = {}
for p in raw_positions:
    outcome = p.get("outcome") or p.get("name") or ""
    slug_for_name[outcome] = p["slug"]

# Parse portfolio command output
r = subprocess.run(["python3", SCRIPT, "portfolio"], capture_output=True, text=True, timeout=60)
output = r.stdout

live_data = []
total_value = 0
total_cost = 0
total_pnl = 0

lines = output.split("\n")
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip().startswith("🟢") or line.strip().startswith("🔴"):
        name = line.strip().replace("🟢", "").replace("🔴", "").replace("**", "").strip()
        
        entry_price = current_price = 0
        shares = 0
        value = pnl_val = pnl_pct = 0
        
        if i+1 < len(lines):
            m = re.search(r'(\d+)\s+shares\s+@\s+(\d+\.?\d*)%\s+→\s+(\d+\.?\d*)%', lines[i+1])
            if m:
                shares = int(m.group(1))
                entry_price = float(m.group(2)) / 100
                current_price = float(m.group(3)) / 100
        
        if i+2 < len(lines):
            vm = re.search(r'Value:\s*\$([0-9,]+\.?\d*)', lines[i+2])
            pm = re.search(r'P&L:\s*\$([+-]?[0-9,]+\.?\d*)\s+\(([+-]?\d+\.?\d*)%\)', lines[i+2])
            if vm: value = float(vm.group(1).replace(",", ""))
            if pm:
                pnl_val = float(pm.group(1).replace(",", ""))
                pnl_pct = float(pm.group(2))
        
        cost = value - pnl_val
        total_value += value
        total_cost += cost
        total_pnl += pnl_val
        
        slug = slug_for_name.get(name, "")
        desc = SLUG_DESCRIPTIONS.get(slug, slug.replace("-", " ").title())
        
        live_data.append({
            "name": name,
            "desc": desc,
            "slug": slug,
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

safe = sorted([p for p in live_data if p["entry_price"] >= 0.5], key=lambda x: x["value"], reverse=True)
yolo = sorted([p for p in live_data if 0.05 <= p["entry_price"] < 0.5], key=lambda x: x["value"], reverse=True)
moonshot = sorted([p for p in live_data if p["entry_price"] < 0.05], key=lambda x: x["value"], reverse=True)

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
.header .sub {{ color: #888; margin-top: 6px; font-size: 0.85em; }}
.target {{ text-align: center; margin: 10px 0; padding: 12px; background: #14141f; border-radius: 12px; border: 1px solid #222; }}
.target .goal {{ font-size: 0.8em; color: #7c4dff; }}
.target .car {{ font-size: 1.4em; }}
.stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 16px 0; }}
@media(min-width:600px) {{ .stats {{ grid-template-columns: repeat(4, 1fr); }} }}
.sc {{ background: #14141f; border-radius: 12px; padding: 14px; border: 1px solid #222; }}
.sc .l {{ color: #888; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; }}
.sc .v {{ font-size: 1.5em; font-weight: 700; margin-top: 4px; }}
.g {{ color: #00d4aa; }} .r {{ color: #ff4757; }} .n {{ color: #e0e0e0; }}
.sec {{ margin: 24px 0; }}
.sec h2 {{ font-size: 1.1em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
.bdg {{ background: #222; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; color: #888; }}
.pos {{ background: #14141f; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; border: 1px solid #222; }}
.pos:hover {{ border-color: #444; }}
.pos .top {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
.pos .nm {{ font-weight: 600; font-size: 0.95em; }}
.pos .desc {{ color: #999; font-size: 0.75em; margin-top: 2px; font-style: italic; }}
.pos .mt {{ color: #666; font-size: 0.75em; margin-top: 3px; }}
.pos .rt {{ text-align: right; }}
.pos .pnl {{ font-size: 1.05em; font-weight: 700; }}
.pos .dt {{ color: #888; font-size: 0.75em; margin-top: 3px; }}
.rt-s {{ display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 0.65em; font-weight: 600; margin-left: 6px; }}
.rt-safe {{ background: #00d4aa22; color: #00d4aa; }}
.rt-yolo {{ background: #ffa50022; color: #ffa500; }}
.rt-moon {{ background: #7c4dff22; color: #7c4dff; }}
.pb {{ width: 100%; height: 8px; background: #222; border-radius: 4px; margin-top: 10px; overflow: hidden; }}
.pf {{ height: 100%; border-radius: 4px; }}
.hist {{ margin-top: 24px; }}
.tr {{ display: flex; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #1a1a2a; font-size: 0.8em; }}
.ft {{ text-align: center; padding: 24px 0; color: #444; font-size: 0.75em; }}
</style>
</head>
<body>
<div class="header">
    <h1>🎰 Lando's Paper Trading</h1>
    <div class="sub">Polymarket • {now}</div>
</div>
<div class="target">
    <div class="car">🚗 G-Wagon Challenge</div>
    <div class="goal">${portfolio_total:,.0f} / $180,000 ({progress:.2f}%)</div>
    <div class="pb"><div class="pf" style="width:{progress:.1f}%;background:linear-gradient(90deg,#00d4aa,#7c4dff);"></div></div>
</div>
<div class="stats">
    <div class="sc"><div class="l">💰 Portföy</div><div class="v n">${portfolio_total:,.2f}</div></div>
    <div class="sc"><div class="l">📊 Yatırılan</div><div class="v n">${total_cost:,.2f}</div></div>
    <div class="sc"><div class="l">📈 P&L</div><div class="v {pnl_color}">{pnl_sign}${total_pnl:,.2f} ({pnl_sign}{total_pnl_pct:.1f}%)</div></div>
    <div class="sc"><div class="l">💵 Nakit</div><div class="v n">${cash:,.2f}</div></div>
</div>
<div style="text-align:center;color:#666;font-size:0.75em;margin:4px 0;">
    {len(live_data)} pozisyon • {len(safe)} güvenli • {len(yolo)} YOLO • {len(moonshot)} moonshot
</div>
"""

def render(positions, emoji, title, rc):
    if not positions: return ""
    ts = sum(p["value"] for p in positions)
    h = f'<div class="sec"><h2>{emoji} {title} <span class="bdg">{len(positions)} pos • ${ts:,.0f}</span></h2>'
    for p in positions:
        pc = "g" if p["pnl"] >= 0 else "r"
        ps = "+" if p["pnl"] >= 0 else ""
        tag = "🛡️ Safe" if rc=="safe" else "🎲 YOLO" if rc=="yolo" else "🌙 Moon"
        pot = ""
        if rc in ("yolo","moon") and p["entry_price"] > 0:
            pot = f' • Tutarsa {1/p["entry_price"]:.0f}x'
        h += f'''<div class="pos">
<div class="top"><div style="flex:1;min-width:180px">
<div class="nm">{p["name"]}<span class="rt-s rt-{rc}">{tag}</span></div>
<div class="desc">{p["desc"]}</div>
<div class="mt">{p["shares"]:.0f} sh @ {p["entry_price"]*100:.1f}% → {p["current_price"]*100:.1f}%{pot}</div>
</div><div class="rt">
<div class="pnl {pc}">{ps}${p["pnl"]:.2f} ({ps}{p["pnl_pct"]:.1f}%)</div>
<div class="dt">${p["cost"]:.0f} → ${p["value"]:.2f}</div>
</div></div></div>'''
    h += '</div>'
    return h

html += render(safe, "🛡️", "Güvenli", "safe")
html += render(yolo, "🎲", "YOLO", "yolo")
html += render(moonshot, "🌙", "Moonshot", "moon")

html += '<div class="hist"><h2>📜 Son Trade\'ler</h2>'
for t in reversed(history[-15:]):
    ac = "g" if t["action"]=="buy" else "r"
    at = "ALIŞ" if t["action"]=="buy" else "SATIŞ"
    ts = t.get("at","")[:16].replace("T"," ")
    slug = t.get("slug","")
    desc = SLUG_DESCRIPTIONS.get(slug, "")
    outcome = t.get("outcome", slug)
    label = f"{outcome}" + (f" ({desc})" if desc else "")
    html += f'<div class="tr"><span class="{ac}">{at}</span><span>{label}</span><span>${t["amount"]:.0f} @ {t["price"]*100:.1f}%</span><span style="color:#666">{ts}</span></div>'

html += f'</div><div class="ft">🎰 Lando Paper Trading • OpenClaw + Polymarket<br>Hedef: G-Wagon ($180K) 🚗 • Auto-refresh: 30dk</div></body></html>'

with open(OUTPUT_PATH, "w") as f:
    f.write(html)
print(f"Dashboard generated - {len(live_data)} positions, P&L: ${total_pnl:+.2f}")
