#!/usr/bin/env python3
"""Shipping cadence: the last 53 weeks of contributions as breathing columns
(the same 'blinds' motif as the hero). Run daily by .github/workflows/cadence.yml.

    GITHUB_TOKEN=... python3 scripts/cadence.py [login]
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date

from kit import EASE, THEMES, Doc, wrap
from knot import knot, slice_path

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


def build_knot(theme, weeks):
    """Endless knot: every day of the year is one segment of a single woven strand."""
    W, H = 1200, 600
    days = [d for w in weeks for d in w]
    D = len(days)
    mx = max(d["contributionCount"] for d in days) or 1
    lit = sum(1 for d in days if d["contributionCount"])
    d = Doc(W, H, theme, f"An endless knot made of {D} days; {lit} of them glow where I shipped code")
    t = d.t
    cx, cy, size = 330, H / 2, 500
    P, cum, over, unit = knot(size, cx, cy)
    total = cum[-1]
    seg = total / D
    SW = round(unit * 0.74, 1)

    def path(pts):
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    def mix(a, b, k):
        a, b = [int(a[i:i+2], 16) for i in (1, 3, 5)], [int(b[i:i+2], 16) for i in (1, 3, 5)]
        return "#" + "".join(f"{round(x + (y - x) * k):02X}" for x, y in zip(a, b))

    tie = 4.6  # seconds for the knot to tie itself
    d.css = f"""
.dd{{animation:dd .35s ease-out both}}
@keyframes dd{{from{{opacity:0}}}}
.now{{transform-box:fill-box;transform-origin:center;animation:now 2.2s ease-out infinite}}
@keyframes now{{from{{transform:scale(1);opacity:.7}}to{{transform:scale(3.2);opacity:0}}}}
.txt{{animation:txt .8s {EASE} both}}@keyframes txt{{from{{opacity:0;transform:translateY(10px)}}}}
"""
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>')
    # intensity level per day: 0 = rest, 1..4 = shipped (3-day smoothed so runs read as ribbons)
    counts = [x["contributionCount"] for x in days]
    sm = [sum(counts[max(0, i - 1):i + 2]) / len(counts[max(0, i - 1):i + 2]) for i in range(D)]
    smx = max(sm) or 1
    level = [0 if not c else 1 + min(3, int(4 * (v / smx) ** 0.5)) for c, v in zip(counts, sm)]
    shades = [t["off"]] + [mix(t["card"], t["primary"], k) for k in (0.42, 0.6, 0.8, 1.0)]

    # corners of the centerline (arc lengths) so colour changes never sit on a bend
    corner_s = []
    for i in range(len(P)):
        a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-6:
            corner_s.append(cum[i])

    # every crossing is visited twice; keep colour changes off both visits too
    def lattice_hits():
        hits = []
        for i in range(len(P)):
            for j in over:
                if i != j and math.dist(P[i], P[j]) < 0.5:
                    hits.append(cum[i])
        return hits
    keepout = sorted(corner_s + [cum[j] for j in over] + lattice_hits())

    def snap(x):
        for _ in range(4):
            moved = False
            for cs in keepout:
                if abs(x - cs) < SW / 2 + 10:
                    x, moved = cs + SW / 2 + 10, True
            if not moved:
                break
        return x

    runs, i = [], 0
    while i < D:
        j = i
        while j + 1 < D and level[j + 1] == level[i]:
            j += 1
        runs.append((i, j, level[i]))
        i = j + 1
    bounds = [0.0] + [snap((r[1] + 1) * seg) for r in runs[:-1]] + [total]
    for k in range(1, len(bounds)):
        bounds[k] = min(total, max(bounds[k], bounds[k - 1]))

    def level_at(x):
        for k, r in enumerate(runs):
            if bounds[k] <= x < bounds[k + 1]:
                return r[2]
        return runs[-1][2]

    edge = t["bg"]
    parts = ['<g>', f'<path d="{path(P)}Z" stroke="{edge}" stroke-width="{SW+2.5}"/>',
             f'<path d="{path(P)}Z" stroke="{t["off"]}"/>']
    for k, (i0, i1, lv) in enumerate(runs):
        if lv == 0 or bounds[k + 1] - bounds[k] < 5:
            continue
        parts.append(f'<path class="dd" style="animation-delay:{i0*tie/D:.3f}s" '
                     f'd="{path(slice_path(P, cum, bounds[k] - 0.8, bounds[k+1] + 0.8))}" stroke="{shades[lv]}"/>')
    # over-crossings: cut a gap in the under strand, redraw the over strand on top
    for idx in over:
        s0 = cum[idx]
        a, b = s0 - (SW / 2 + 9), s0 + (SW / 2 + 9)
        seg_pts = path(slice_path(P, cum, a, b))
        lv = level_at(s0)
        when = (int(s0 // seg) % D) * tie / D
        parts.append(f'<g class="dd" style="animation-delay:{when:.3f}s">'
                     f'<path d="{seg_pts}" stroke="{t["card"]}" stroke-width="{SW+5}"/>'
                     f'<path d="{seg_pts}" stroke="{edge}" stroke-width="{SW+2.5}"/>'
                     f'<path d="{seg_pts}" stroke="{shades[lv]}"/></g>')
    # today = end of the strand
    end = slice_path(P, cum, total - 1, total)[-1]
    parts.append(f'<g class="dd" style="animation-delay:{tie:.2f}s"><circle class="now" cx="{end[0]:.1f}" cy="{end[1]:.1f}" r="{SW/2:.1f}" fill="{t["primary"]}"/>'
                 f'<circle cx="{end[0]:.1f}" cy="{end[1]:.1f}" r="{SW/2-1:.1f}" fill="{t["fg"]}" stroke="{t["card"]}" stroke-width="3"/></g>')
    parts.append("</g>")
    d.add(f'<g fill="none" stroke-width="{SW}" stroke-linejoin="miter" stroke-miterlimit="4">' + "".join(parts) + "</g>")

    x = 660
    d.add('<g class="txt" style="animation-delay:.3s">')
    d.add(d.tspan_text(x, 150, [("ENDLESS KNOT · PALBEU", t["primary"], None), (f"  ·  {D} DAYS", t["muted"], None)], "m", 13, 0.18))
    yy = 206
    for ln in ["One line.", "No beginning, no end."]:
        d.add(d.text(x - 2, yy, ln, "h", 44, t["fg"], -0.035))
        yy += 52
    yy += 14
    body = ("Every day of my last year is one segment of a single unbroken strand, woven over and under itself. "
            "It glows where I shipped and dims where I rested. It ties itself again every morning.")
    for ln in wrap(body, 470, "b", 18):
        d.add(d.text(x, yy, ln, "b", 18, t["muted"]))
        yy += 29
    yy += 30
    # legend
    lx = x
    d.add(f'<path d="M{lx} {yy}h34" stroke="{t["off"]}" stroke-width="12"/>')
    d.add(d.text(lx + 46, yy + 5, "REST", "m", 12, t["muted"], 0.16))
    lx += 120
    for j, op in enumerate([0.4, 0.65, 1.0]):
        d.add(f'<path d="M{lx + j*20} {yy}h18" stroke="{mix(t["card"], t["primary"], op)}" stroke-width="12"/>')
    d.add(d.text(lx + 72, yy + 5, "SHIPPED", "m", 12, t["muted"], 0.16))
    lx += 190
    d.add(f'<circle cx="{lx+6}" cy="{yy}" r="6" fill="{t["fg"]}"/>')
    d.add(d.text(lx + 22, yy + 5, "TODAY", "m", 12, t["muted"], 0.16))
    d.add(d.text(x, H - 52, f"{lit} OF {D} DAYS LIT", "m", 12.5, t["fg"], 0.16))
    d.add("</g>")
    d.save("knot.svg", theme)


if __name__ == "__main__":
    total, weeks = fetch()
    for th in THEMES:
        build_knot(th, weeks)
    print(f"knot: {total} contributions")
