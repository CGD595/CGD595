#!/usr/bin/env python3
"""Shipping cadence: the last 53 weeks of contributions as breathing columns
(the same 'blinds' motif as the hero). Run daily by .github/workflows/cadence.yml.

    GITHUB_TOKEN=... python3 scripts/cadence.py [login]
"""
import json
import os
import sys
import urllib.request
from datetime import date

from kit import EASE, THEMES, Doc

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "CGD595"
QUERY = """query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{contributionCount date}}}}}}"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "cadence-svg"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [w["contributionDays"] for w in cal["weeks"]]


def longest_streak(days):
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] else 0
        best = max(best, cur)
    return best


def build(theme, total, weeks):
    W, H = 1200, 420
    days = [d for w in weeks for d in w]
    weekly = [sum(d["contributionCount"] for d in w) for w in weeks]
    n, mx = len(weekly), max(weekly) or 1
    peak = weekly.index(mx)
    stats = [
        (f"{total:,}", "Contributions · 12 mo"),
        (str(sum(1 for d in days if d["contributionCount"])), "Active days"),
        (str(longest_streak(days)), "Longest streak"),
        (str(max(d["contributionCount"] for d in days)), "Best day"),
    ]
    d = Doc(W, H, theme, f"{total} contributions in the last year, one column per week")
    t = d.t
    d.css = f"""
.col{{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1.1s {EASE} both,breathe 4s ease-in-out infinite}}
@keyframes grow{{from{{transform:scaleY(0)}}}}
@keyframes breathe{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
.s{{animation:s .8s {EASE} both}}@keyframes s{{from{{opacity:0;transform:translateY(10px)}}}}
"""
    d.defs.append(
        f'<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["primary"]}"/>'
        f'<stop offset="1" stop-color="{t["primary"]}" stop-opacity=".12"/></linearGradient>'
        f'<linearGradient id="g0" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["primary"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{t["primary"]}" stop-opacity=".06"/></linearGradient>'
    )
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>')
    cw = (W - 72) / 4
    for i, (v, label) in enumerate(stats):
        x = 36 + i * cw
        d.add(f'<g class="s" style="animation-delay:{i*0.08:.2f}s">'
              + d.text(x, 82, v, "h", 44, t["fg"], -0.04)
              + d.text(x + 2, 112, label.upper(), "m", 12, t["muted"], 0.16) + "</g>")

    base, top = 350, 168
    x0, x1 = 36, W - 36
    step = (x1 - x0) / n
    bw = step - 5
    d.add(f'<path d="M{x0} {base+.5}H{x1}" stroke="{t["border"]}"/>')
    for i, v in enumerate(weekly):
        h = max(3, (base - top) * (v / mx) ** 0.6) if v else 3
        x = x0 + i * step + 2.5
        fill = "url(#g)" if v else t["border"]
        d.add(f'<rect class="col" x="{x:.1f}" y="{base-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" fill="{fill}" '
              f'style="animation-delay:{0.2+i*0.02:.2f}s,{1.5+(i%7)*0.45:.2f}s"/>')
    px = x0 + peak * step + 2.5 + bw / 2
    label = "PEAK · WEEK OF " + date.fromisoformat(weeks[peak][0]["date"]).strftime("%b %d").upper() + f" · {mx}"
    anchor = "end" if px > W - 260 else "start"
    lx = px + (8 if anchor == "start" else -8)
    d.add(f'<path d="M{px:.1f} {top-6}V{top-26}" stroke="{t["primary"]}"/>')
    d.add(d.text(lx, top - 16, label, "m", 12, t["primary"], 0.14, anchor=anchor))

    last = None
    for i, w in enumerate(weeks):
        m = date.fromisoformat(w[0]["date"]).strftime("%b").upper()
        if m != last and 0 < i < n - 2:
            d.add(d.text(x0 + i * step + 2.5, base + 30, m, "m", 11.5, t["faint"], 0.14))
        last = m
    d.add(d.text(W - 36, H - 22 + 2, f"UPDATED {date.today():%d.%m.%Y}", "m", 11, t["faint"], 0.14, anchor="end"))
    d.save("cadence.svg", theme)


if __name__ == "__main__":
    total, weeks = fetch()
    for th in THEMES:
        build(th, total, weeks)
    print(f"cadence: {total} contributions")
