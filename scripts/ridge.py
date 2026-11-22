#!/usr/bin/env python3
"""Contribution Himalaya: turns the last year of GitHub contributions into a mountain range.

Each week is a point on the ridge; busier weeks make taller peaks. The busiest
peaks get snow, and a string of prayer flags hangs between the two highest.

Usage:  GITHUB_TOKEN=... python3 scripts/ridge.py [login]
Stdlib only, so the Action needs no installs.
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

LOGIN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_LOGIN", "CGD595")
OUT = Path(__file__).resolve().parent.parent / "assets" / "ridge.svg"

BG, PANEL, LINE, INK, MUTED, DIM = "#0A0E17", "#0F1522", "#1E2738", "#EAEFF7", "#8A95A8", "#5B6578"
FLAGS = ["#3E8BFF", "#E9EEF6", "#F0524F", "#2FBF71", "#F6B940"]
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace"


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    q = """query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{contributionCount date}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "contribution-ridge"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [w["contributionDays"] for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def smooth(v, k):
    out = []
    for i in range(len(v)):
        lo, hi = max(0, i - k), min(len(v), i + k + 1)
        out.append(sum(v[lo:hi]) / (hi - lo))
    return out


def catmull(pts):
    """Smooth path through points (Catmull-Rom -> cubic Bezier)."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def jagged(pts, seed_vals):
    """Add rock-like detail between points so it reads as mountains, not a chart."""
    out = []
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        out.append((x1, y1))
        mx = (x1 + x2) / 2
        jitter = ((seed_vals[i] * 7919) % 13 - 6) * 0.9
        out.append((mx, (y1 + y2) / 2 + jitter))
    out.append(pts[-1])
    return out


def build(total, weeks):
    W, H = 1200, 400
    top, base = 110, 330
    weekly = [sum(d["contributionCount"] for d in w) for w in weeks]
    n = len(weekly)
    mx = max(weekly) or 1
    scale = lambda v: (v / mx) ** 0.55  # sqrt-ish so small weeks still show

    xs = [40 + i * (W - 80) / (n - 1) for i in range(n)]

    def layer(vals, height, lift):
        pts = [(xs[i], base - lift - height * scale(v)) for i, v in enumerate(vals)]
        return [(0, base - lift)] + pts + [(W, base - lift)]

    back = layer(smooth(weekly, 4), (base - top) * 0.95, 0)
    mid = layer(smooth(weekly, 1), base - top, 0)
    front_vals = smooth(weekly, 0)
    front = jagged(layer(front_vals, (base - top) * 0.62, -18), [int(v) + i for i, v in enumerate(front_vals + [0, 0])])

    def area(pts, smooth_curve=True):
        line = catmull(pts) if smooth_curve else "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        return f"{line} L{W} {H} L0 {H} Z", line

    back_a, _ = area(back)
    mid_a, mid_line = area(mid, False)
    front_a, _ = area(front, False)

    # peaks: top weeks get snow + labels
    order = sorted(range(n), key=lambda i: weekly[i], reverse=True)
    peaks = []
    for i in order:
        if all(abs(i - j) > 4 for j in peaks):
            peaks.append(i)
        if len(peaks) == 2:
            break
    peak = peaks[0]
    py = mid[peak + 1][1]
    snow_line = py + 34

    # prayer flags between the two highest peaks
    flags = ""
    if len(peaks) == 2:
        a, b = sorted(peaks)
        (x0, y0), (x1, y1) = mid[a + 1], mid[b + 1]
        y0 -= 2
        y1 -= 2
        cx, cy = (x0 + x1) / 2, max(y0, y1) + 40
        k = max(6, int(abs(x1 - x0) / 22))
        bits = [f'<path d="M{x0:.1f} {y0:.1f} Q{cx:.1f} {cy:.1f} {x1:.1f} {y1:.1f}" stroke="#C9D2E0" stroke-opacity=".6" fill="none"/>']
        for j in range(k):
            u = (j + 0.5) / k
            x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u ** 2 * x1
            y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u ** 2 * y1
            bits.append(
                f'<g transform="translate({x:.1f} {y:.1f})"><rect class="flag" style="animation-delay:{-(j*0.4)%3:.1f}s" '
                f'x="-5" y="0" width="10" height="14" rx="1" fill="{FLAGS[j%5]}" fill-opacity=".92"/></g>'
            )
        flags = "".join(bits)

    peak_week = weeks[peak][0]["date"]
    peak_label = date.fromisoformat(peak_week).strftime("%b %d, %Y")
    best_day = max((d for w in weeks for d in w), key=lambda d: d["contributionCount"])
    active_days = sum(1 for w in weeks for d in w if d["contributionCount"] > 0)

    # month ticks
    ticks = []
    last = None
    for i, w in enumerate(weeks):
        m = date.fromisoformat(w[0]["date"]).strftime("%b")
        if m != last and i < n - 2:
            ticks.append(f'<text x="{xs[i]:.1f}" y="{base+50}" class="mono" font-size="11" fill="{DIM}">{m}</text>')
            last = m

    stars = "".join(
        f'<circle cx="{(i*137.5)%W:.1f}" cy="{(i*61.7)%110+100:.1f}" r="{0.6+(i%3)*0.35:.2f}" fill="#fff" class="tw" '
        f'style="animation-delay:{-(i*0.53)%5:.1f}s"/>' for i in range(60)
    )

    stat = lambda x, big, small, c: (
        f'<text x="{x}" y="58" class="sans" font-size="30" font-weight="800" letter-spacing="-1" fill="{c}">{big}</text>'
        f'<text x="{x}" y="80" class="mono" font-size="11.5" letter-spacing="1.5" fill="{MUTED}">{small}</text>'
    )

    css = f"""
.sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}
.tw{{animation:tw 4s ease-in-out infinite}}@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}
.flag{{transform-box:fill-box;transform-origin:50% 0;animation:sway 3s ease-in-out infinite}}
@keyframes sway{{0%,100%{{transform:rotate(-8deg) skewY(-3deg)}}50%{{transform:rotate(8deg) skewY(3deg)}}}}
.draw{{stroke-dasharray:4000;animation:draw 3.2s cubic-bezier(.4,0,.2,1) both}}
@keyframes draw{{from{{stroke-dashoffset:4000}}to{{stroke-dashoffset:0}}}}
.rise{{transform-origin:0 {base}px;animation:rise 1.6s cubic-bezier(.2,.7,.2,1) both}}
@keyframes rise{{from{{transform:scaleY(.15);opacity:0}}to{{transform:none;opacity:1}}}}
.pin{{animation:pin .6s 2.2s both}}@keyframes pin{{from{{opacity:0}}to{{opacity:1}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
"""
    px = xs[peak]
    body = f"""
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070D"/><stop offset="1" stop-color="#151A30"/></linearGradient>
  <linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#26304B"/><stop offset="1" stop-color="#121829"/></linearGradient>
  <linearGradient id="m" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A4A73"/><stop offset=".5" stop-color="#1B2338"/><stop offset="1" stop-color="#0F1522"/></linearGradient>
  <clipPath id="snow"><rect width="{W}" height="{snow_line:.0f}"/></clipPath>
  <clipPath id="fr"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#fr)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{stars}
{stat(40, f"{total:,}", "CONTRIBUTIONS · 12 MO", INK)}
{stat(300, f"{active_days}", "ACTIVE DAYS", FLAGS[3])}
{stat(500, f"{best_day['contributionCount']}", "BEST DAY", "#F6B940")}
{stat(680, f"{weekly[peak]}", "SUMMIT WEEK", FLAGS[0])}
<text x="{W-40}" y="40" text-anchor="end" class="mono" font-size="11" fill="{DIM}">updated {date.today().isoformat()}</text>
<g class="rise">
  <path d="{back_a}" fill="url(#b)"/>
  <path d="{mid_a}" fill="url(#m)"/>
  <path d="{mid_a}" fill="#EEF2F8" fill-opacity=".9" clip-path="url(#snow)"/>
  {flags}
  <path d="{front_a}" fill="{BG}"/>
</g>
<path d="{mid_line}" class="draw" stroke="#9DB4E8" stroke-opacity=".55" stroke-width="1.3" fill="none"/>
<g class="pin">
  <line x1="{px:.1f}" y1="{py-8:.1f}" x2="{px:.1f}" y2="{py-34:.1f}" stroke="{INK}" stroke-opacity=".7"/>
  <text x="{px:.1f}" y="{py-42:.1f}" text-anchor="middle" class="mono" font-size="11.5" fill="{INK}">summit · wk of {peak_label}</text>
</g>
{''.join(ticks)}
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{LINE}"/>
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{total} contributions in the last year, drawn as a mountain range">'
            f"<style>{css}</style>{body}</svg>\n")


if __name__ == "__main__":
    total, weeks = fetch()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build(total, weeks), encoding="utf-8")
    print(f"wrote {OUT} ({total} contributions)")
