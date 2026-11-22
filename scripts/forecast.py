#!/usr/bin/env python3
"""Commit forecast: a daily weather report for my coding, that grades itself.

Model (per day, P(I ship at least one contribution)):
  blend of three estimates, each Laplace-smoothed
    - weekday rate      same weekday over the last 12 weeks
    - momentum          share of the last 7 days that were active
    - transition        P(active | yesterday active / rested), last 90 days
  The blend weights are fit by maximum likelihood on older history only,
  never on the 180 days the model is graded on.

Every live forecast is appended to data/forecast-log.json (so git history is
the receipt). Days before the first live run are graded with a walk-forward
backtest (no lookahead), and drawn hollow so the two are never confused.

    GITHUB_TOKEN=... python3 scripts/forecast.py [login]
"""
import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from kit import EASE, ROOT, THEMES, Doc, measure

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "CGD595"
LOG = ROOT / "data" / "forecast-log.json"
BTT = timezone(timedelta(hours=6))
GRADE_DAYS, FIT_DAYS = 180, 100


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    q = """query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{
      weeks{contributionDays{contributionCount date}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=json.dumps({"query": q, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "forecast-svg"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    days = [d for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    return [date.fromisoformat(d["date"]) for d in days], [d["contributionCount"] for d in days]


# ---------------------------------------------------------------- model
def estimates(a, t, prev_p=None):
    """Three estimates for day t from activity a[:t]. prev_p replaces a[t-1] when unknown."""
    same = [a[i] for i in range(t - 7, max(-1, t - 7 * 13), -7) if i >= 0]
    dow = (sum(same) + 1) / (len(same) + 2)
    last7 = a[max(0, t - 7):t]
    mom = (sum(last7) + 1) / (len(last7) + 2)
    lo = max(1, t - 90)
    aa = sum(1 for i in range(lo, t) if a[i - 1] and a[i])
    ar = sum(1 for i in range(lo, t) if a[i - 1] and not a[i])
    ra = sum(1 for i in range(lo, t) if not a[i - 1] and a[i])
    rr = sum(1 for i in range(lo, t) if not a[i - 1] and not a[i])
    p_aa, p_ra = (aa + 1) / (aa + ar + 2), (ra + 1) / (ra + rr + 2)
    y = a[t - 1] if prev_p is None else prev_p
    trans = y * p_aa + (1 - y) * p_ra
    return dow, mom, trans


def predict(w, a, t, prev_p=None):
    e = estimates(a, t, prev_p)
    return min(0.97, max(0.03, sum(wi * ei for wi, ei in zip(w, e))))


def fit(a, start, end):
    best, best_ll = None, -1e18
    for i in range(11):
        for j in range(11 - i):
            w = (i / 10, j / 10, (10 - i - j) / 10)
            ll = sum(math.log(p if a[t] else 1 - p) for t in range(start, end) for p in [predict(w, a, t)])
            if ll > best_ll:
                best, best_ll = w, ll
    return best


# ---------------------------------------------------------------- weather words
def condition(p):
    if p >= 0.8:
        return "storm", "Heavy shipping"
    if p >= 0.6:
        return "rain", "Commits likely"
    if p >= 0.4:
        return "mixed", "Scattered commits"
    if p >= 0.2:
        return "cloud", "Mostly quiet"
    return "sun", "Clear skies, rest day"


def icon(kind, x, y, s, color, anim=True):
    """Line-art weather icon centred at (x,y), scale s (1 = 100px box)."""
    sw = 2.6 / s if s > 0.6 else 3.2 / s
    cloud = ("M-30 18 H30 A18 18 0 0 0 26 -16 A26 26 0 0 0 -22 -14 A18 18 0 0 0 -30 18 Z")
    out = [f'<g transform="translate({x:.1f} {y:.1f}) scale({s})" fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round">']
    if kind in ("sun", "mixed"):
        cx, cy, r = (0, 0, 18) if kind == "sun" else (16, -18, 13)
        rays = "".join(f'<path d="M{cx + math.cos(k*math.pi/4)*(r+7):.1f} {cy + math.sin(k*math.pi/4)*(r+7):.1f} '
                       f'L{cx + math.cos(k*math.pi/4)*(r+14):.1f} {cy + math.sin(k*math.pi/4)*(r+14):.1f}"/>' for k in range(8))
        spin = ' class="spin"' if anim else ""
        out.append(f'<g{spin} style="transform-origin:{cx}px {cy}px"><circle cx="{cx}" cy="{cy}" r="{r}"/>{rays}</g>')
    if kind != "sun":
        out.append(f'<path d="{cloud}" fill="{color}" fill-opacity=".08"/>')
    if kind in ("rain", "storm"):
        n = 3 if kind == "rain" else 5
        for k in range(n):
            dx = -20 + k * (40 / (n - 1))
            cls = ' class="drop"' if anim else ""
            out.append(f'<path{cls} style="animation-delay:{k*0.23:.2f}s" d="M{dx:.1f} 28 l-4 10"/>')
    if kind == "storm":
        out.append(f'<path d="M4 22 l-8 14 h8 l-6 12" stroke-width="{sw*1.1:.2f}"/>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- render
def render(theme, info):
    W, H = 1200, 620
    d = Doc(W, H, theme, f"Commit forecast: {round(info['p']*100)}% chance of shipping today")
    t = d.t
    d.css = f"""
.spin{{animation:spin 24s linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}
.drop{{animation:drop 1.1s ease-in infinite}}@keyframes drop{{0%{{transform:translateY(-6px);opacity:0}}30%{{opacity:1}}100%{{transform:translateY(10px);opacity:0}}}}
.in{{animation:in .7s {EASE} both}}@keyframes in{{from{{opacity:0;transform:translateY(10px)}}}}
.tick{{transform-box:fill-box;transform-origin:50% 100%;animation:tk .5s {EASE} both}}@keyframes tk{{from{{transform:scaleY(0)}}}}
"""
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>')
    x = 44
    d.add(d.tspan_text(x, 64, [("COMMIT FORECAST", t["primary"], None),
                              (f"  ·  ISSUED {info['issued']}", t["muted"], None)], "m", 12.5, 0.16))

    # headline
    kind, words = condition(info["p"])
    d.add(f'<g class="in">{icon(kind, x + 62, 160, 1.25, t["primary"])}</g>')
    pct = f"{round(info['p']*100)}%"
    d.add(f'<g class="in" style="animation-delay:.1s">' + d.text(x + 150, 192, pct, "h", 96, t["fg"], -0.05) + "</g>")
    pw = measure(pct, "h", 96, -0.05)
    d.add(f'<g class="in" style="animation-delay:.2s">'
          + d.text(x + 150 + pw + 18, 150, "chance of shipping", "h", 26, t["fg"], -0.02)
          + d.text(x + 150 + pw + 18, 184, "today.", "h", 26, t["fg"], -0.02) + "</g>")
    d.add(d.text(x + 152, 236, f"{words} · expected {info['volume']} contributions if I do", "b", 17, t["muted"]))

    # yesterday's call
    yx = 820
    y = info["yesterday"]
    if y:
        hit = (y["p"] >= 0.5) == y["shipped"]
        d.add(d.text(yx, 120, "YESTERDAY'S CALL", "m", 11.5, t["muted"], 0.16))
        d.add(d.text(yx, 158, f"{round(y['p']*100)}%", "h", 34, t["fg"], -0.03))
        d.add(d.text(yx + measure(f"{round(y['p']*100)}%", "h", 34, -0.03) + 14, 156,
                     f"→ {'shipped ' + str(y['count']) if y['shipped'] else 'rested'}", "b", 18, t["muted"]))
        d.add(d.text(yx, 190, "✓ CALLED IT" if hit else "✗ MISSED", "m", 12.5, t["primary"] if hit else t["muted"], 0.16))

    # 7-day outlook
    oy = 290
    d.add(d.text(x, oy, "7-DAY OUTLOOK", "m", 11.5, t["muted"], 0.16))
    tw = (W - 2 * x - 6 * 12) / 7
    for i, (day, p) in enumerate(info["outlook"]):
        tx = x + i * (tw + 12)
        k, _ = condition(p)
        d.add(f'<g class="in" style="animation-delay:{0.3+i*0.06:.2f}s">'
              f'<rect x="{tx:.1f}" y="{oy+16}" width="{tw:.1f}" height="132" rx="12" fill="{t["bg"] if i else t["primary"]}" '
              f'fill-opacity="{1 if i else 0.08}" stroke="{t["primary"] if i == 0 else t["border"]}"/>')
        d.add(d.text(tx + 16, oy + 44, ("TODAY" if i == 0 else day.strftime("%a").upper()), "m", 11.5,
                     t["primary"] if i == 0 else t["muted"], 0.16))
        d.add(icon(k, tx + tw - 34, oy + 52, 0.42, t["primary"] if p >= 0.4 else t["muted"], anim=False))
        d.add(d.text(tx + 15, oy + 124, f"{round(p*100)}%", "h", 30, t["fg"], -0.03))
        d.add("</g>")

    # track record
    ry = 500
    acc, n_live = info["accuracy"], info["live_days"]
    d.add(d.text(x, ry, "TRACK RECORD · LAST 180 DAYS", "m", 11.5, t["muted"], 0.16))
    cw, gap = 3, 1
    for i, g in enumerate(info["record"]):
        cx0 = x + i * (cw + gap)
        hit = (g["p"] >= 0.5) == g["shipped"]
        h = 10 + 30 * g["p"]
        fill = t["primary"] if hit else t["muted"]
        attr = (f'fill="{fill}"' if g["live"] else f'fill="{fill}" fill-opacity=".14" stroke="{fill}" stroke-width="1.2"')
        d.add(f'<rect class="tick" style="animation-delay:{0.5+i*0.02:.2f}s" x="{cx0}" y="{ry+58-h:.1f}" width="{cw}" height="{h:.1f}" rx="1.5" {attr}/>')
        if not hit:
            d.add(f'<circle cx="{cx0 + cw/2:.1f}" cy="{ry+68}" r="2" fill="{t["muted"]}"/>')
    sx = x + GRADE_DAYS * (cw + gap) + 36
    d.add(d.text(sx, ry + 40, f"{round(acc*100)}%", "h", 40, t["fg"], -0.04))
    d.add(d.text(sx + measure(f"{round(acc*100)}%", "h", 40, -0.04) + 14, ry + 22, "CALLED CORRECTLY", "m", 11.5, t["muted"], 0.16))
    d.add(d.text(sx + measure(f"{round(acc*100)}%", "h", 40, -0.04) + 14, ry + 42, f"BRIER {info['brier']:.2f} · BASELINE {info['baseline']:.0%}", "m", 11.5, t["muted"], 0.16))
    legend = (f"Bar height = predicted chance · dot = missed call · solid = live ({n_live} so far), hollow = walk-forward backtest, no lookahead"
              if n_live < GRADE_DAYS else "Every bar is a live forecast, logged in git before the day happened")
    d.add(d.text(x, H - 30, legend, "b", 13.5, t["faint"]))
    d.save("forecast.svg", theme)


def streak_now(counts, T):
    n = 0
    for i in range(T - 1, -1, -1):
        if not counts[i]:
            break
        n += 1
    return n + (1 if counts[T] else 0)


def render_weather(theme, info, dates, counts):
    """Past year (daily) -> NOW -> next 7 days, in one timeline."""
    W, H = 1200, 640
    d = Doc(W, H, theme, f"Shipping forecast: {round(info['p']*100)}% chance of shipping today; "
                         f"{sum(counts):,} contributions in the last year")
    t = d.t
    T = len(counts) - 1
    d.css = f"""
.spin{{animation:spin 24s linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}
.drop{{animation:drop 1.1s ease-in infinite}}@keyframes drop{{0%{{transform:translateY(-6px);opacity:0}}30%{{opacity:1}}100%{{transform:translateY(10px);opacity:0}}}}
.in{{animation:in .7s {EASE} both}}@keyframes in{{from{{opacity:0;transform:translateY(10px)}}}}
.b{{transform-box:fill-box;transform-origin:50% 100%;animation:g .6s {EASE} both}}@keyframes g{{from{{transform:scaleY(0)}}}}
.now{{animation:nw 2.4s ease-in-out infinite}}@keyframes nw{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
.fz{{animation:in .8s {EASE} both;animation-delay:1.6s}}
"""
    d.defs.append(
        f'<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["primary"]}"/>'
        f'<stop offset="1" stop-color="{t["primary"]}" stop-opacity=".25"/></linearGradient>'
        f'<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="6" height="6" fill="{t["primary"]}" fill-opacity=".05"/><path d="M0 0V6" stroke="{t["primary"]}" stroke-opacity=".12" stroke-width="2"/></pattern>'
    )
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>')
    x = 44
    d.add(d.tspan_text(x, 60, [("SHIPPING WEATHER", t["primary"], None),
                              (f"  ·  ISSUED {info['issued']}", t["muted"], None)], "m", 12.5, 0.16))

    # ---- headline (today)
    kind, words = condition(info["p"])
    d.add(f'<g class="in">{icon(kind, x + 54, 140, 1.05, t["primary"])}</g>')
    pct = f"{round(info['p']*100)}%"
    d.add('<g class="in" style="animation-delay:.1s">' + d.text(x + 128, 168, pct, "h", 84, t["fg"], -0.05) + "</g>")
    pw = measure(pct, "h", 84, -0.05)
    d.add('<g class="in" style="animation-delay:.2s">'
          + d.text(x + 128 + pw + 16, 132, "chance of shipping", "h", 23, t["fg"], -0.02)
          + d.text(x + 128 + pw + 16, 162, "today.", "h", 23, t["fg"], -0.02) + "</g>")
    d.add(d.text(x + 130, 206, f"{words} · expected {info['volume']} contributions if I do", "b", 16, t["muted"]))

    # ---- right column: yesterday + track record
    rx = 800
    y = info["yesterday"]
    hit = (y["p"] >= 0.5) == y["shipped"]
    d.add(d.text(rx, 104, "YESTERDAY", "m", 11.5, t["muted"], 0.16))
    d.add(d.text(rx, 138, f"{round(y['p']*100)}%", "h", 30, t["fg"], -0.03))
    yw = measure(f"{round(y['p']*100)}%", "h", 30, -0.03)
    d.add(d.text(rx + yw + 12, 136, f"→ {'shipped ' + str(y['count']) if y['shipped'] else 'rested'}", "b", 16, t["muted"]))
    d.add(d.text(rx, 160, "✓ CALLED IT" if hit else "✗ MISSED", "m", 11.5, t["primary"] if hit else t["muted"], 0.16))
    rx2 = 990
    d.add(d.text(rx2, 104, f"LAST {GRADE_DAYS} DAYS", "m", 11.5, t["muted"], 0.16))
    d.add(d.text(rx2, 138, f"{round(info['accuracy']*100)}%", "h", 30, t["fg"], -0.03))
    aw = measure(f"{round(info['accuracy']*100)}%", "h", 30, -0.03)
    d.add(d.text(rx2 + aw + 10, 136, "correct", "b", 16, t["muted"]))
    d.add(d.text(rx2, 160, f"BASELINE {info['baseline']:.0%} · BRIER {info['brier']:.2f}", "m", 11.5, t["muted"], 0.14))

    # ---- timeline
    top, base = 262, 470
    x0, x1 = x, W - x
    fz = 196                      # forecast zone width
    now_x = x1 - fz
    n = T                         # completed days drawn (today lives in the forecast zone)
    step = (now_x - 10 - x0) / n
    bw = max(1.2, step * 0.72)
    mx = max(counts[:T]) or 1
    hh = lambda v: (base - top) * (v / mx) ** 0.5
    d.add(f'<path d="M{x0} {base+.5}H{x1}" stroke="{t["border"]}"/>')
    graded = {len(counts) - 1 - 1 - k for k in range(GRADE_DAYS)}
    rec_by_i = {T - GRADE_DAYS + k: g for k, g in enumerate(info["record"])}
    for i in range(n):
        v = counts[i]
        bx = x0 + i * step
        if v:
            h = max(2, hh(v))
            d.add(f'<rect class="b" style="animation-delay:{i*0.003:.3f}s" x="{bx:.2f}" y="{base-h:.1f}" width="{bw:.2f}" height="{h:.1f}" fill="url(#g)"/>')
        g = rec_by_i.get(i)
        if g and ((g["p"] >= 0.5) != g["shipped"]):
            d.add(f'<circle cx="{bx+bw/2:.1f}" cy="{base+12}" r="2.2" fill="{t["muted"]}"/>')
    # graded bracket
    gx = x0 + (T - GRADE_DAYS) * step
    d.add(f'<path d="M{gx:.1f} {base+22}V{base+26}H{now_x-10:.1f}V{base+22}" fill="none" stroke="{t["border"]}"/>')
    d.add(d.text(gx, base + 42, f"GRADED · DOTS = MISSED CALLS", "m", 10.5, t["faint"], 0.14))
    # month ticks
    last = None
    for i in range(n):
        m = dates[i].strftime("%b").upper()
        if m != last and 3 < i < n - 8 and dates[i].day <= 7:
            d.add(d.text(x0 + i * step, top - 8, m, "m", 10.5, t["faint"], 0.14))
        last = m

    # forecast zone
    d.add(f'<g class="fz"><rect x="{now_x:.1f}" y="{top-24}" width="{fz}" height="{base-top+24}" rx="8" fill="url(#hatch)"/>')
    d.add(f'<path class="now" d="M{now_x:.1f} {top-30}V{base+4}" stroke="{t["primary"]}" stroke-width="1.5"/>')
    d.add(d.text(now_x + 8, top - 30, "NOW", "m", 10.5, t["primary"], 0.16))
    d.add(d.text(x1 - 6, top - 30, "NEXT 7 DAYS", "m", 10.5, t["muted"], 0.16, anchor="end"))
    fstep = (fz - 16) / 7
    for k, (day, p) in enumerate(info["outlook"]):
        fx = now_x + 10 + k * fstep
        ev = info["expect"][k]
        h = max(4, hh(ev)) if ev else 4
        fw = fstep * 0.66
        d.add(f'<rect x="{fx:.1f}" y="{base-h:.1f}" width="{fw:.1f}" height="{h:.1f}" rx="2" fill="{t["primary"]}" '
              f'fill-opacity="{0.1 + 0.25*p:.2f}" stroke="{t["primary"]}" stroke-dasharray="3 3" stroke-opacity=".8"/>')
        d.add(d.text(fx + fw / 2, base - h - 8, f"{round(p*100)}", "m", 11, t["fg"] if k == 0 else t["muted"], anchor="middle"))
        d.add(d.text(fx + fw / 2, base + 16, ("T" if k == 0 else day.strftime("%a")[0]), "m", 10.5,
                     t["primary"] if k == 0 else t["faint"], 0.1, anchor="middle"))
    d.add("</g>")

    # ---- footer stats
    sy = H - 44
    stats = [(f"{sum(counts):,}", "contributions · 12 mo"), (str(sum(1 for c in counts if c)), "active days"),
             (str(streak_now(counts, T)), "day streak"), (str(max(counts)), "best day")]
    sx = x
    for v, label in stats:
        d.add(d.text(sx, sy, v, "h", 24, t["fg"], -0.03))
        vw = measure(v, "h", 24, -0.03)
        d.add(d.text(sx + vw + 8, sy - 1, label.upper(), "m", 11, t["muted"], 0.14))
        sx += vw + 8 + measure(label.upper(), "m", 11, 0.14) + 40
    d.add(d.text(x1, sy - 1, "FORECAST % ABOVE BARS · DASHED = EXPECTED", "m", 10.5, t["faint"], 0.14, anchor="end"))
    d.save("weather.svg", theme)


# ---------------------------------------------------------------- main
def main():
    dates, counts = fetch()
    a = [1 if c else 0 for c in counts]
    T = len(a) - 1                      # index of today (partial, never used as data)
    last_full = T - 1
    grade_lo = last_full - GRADE_DAYS + 1
    w = fit(a, max(91, grade_lo - FIT_DAYS), grade_lo)

    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    today = dates[T]
    p_today = predict(w, a, T)
    # only a forecast issued before 09:00 Bhutan time counts as a live prediction
    if datetime.now(BTT).hour < 9 and today.isoformat() not in log:
        log[today.isoformat()] = {"p": round(p_today, 4), "issued": datetime.now(BTT).isoformat(timespec="minutes")}
        LOG.parent.mkdir(exist_ok=True)
        LOG.write_text(json.dumps(dict(sorted(log.items())), indent=1) + "\n")

    record = []
    for i in range(grade_lo, last_full + 1):
        key = dates[i].isoformat()
        live = key in log
        p = log[key]["p"] if live else predict(w, a, i)
        record.append({"p": p, "shipped": bool(a[i]), "count": counts[i], "live": live})
    acc = sum((g["p"] >= 0.5) == g["shipped"] for g in record) / len(record)
    brier = sum((g["p"] - g["shipped"]) ** 2 for g in record) / len(record)
    base_rate = sum(a[grade_lo:last_full + 1]) / len(record)
    baseline = max(base_rate, 1 - base_rate)  # accuracy of always guessing the majority

    outlook, prev = [], None
    aa = list(a[:T])
    for k in range(7):
        p = predict(w, aa, T + k, prev) if k else p_today
        outlook.append((today + timedelta(days=k), p))
        aa.append(p)  # expected activity feeds momentum for later days
        prev = p
    # weekday volume: interquartile range of active same-weekday counts
    same = sorted(c for i, c in enumerate(counts[:T]) if c and (T - i) % 7 == 0 and T - i <= 84) or sorted(c for c in counts[:T] if c)
    q = lambda f: same[min(len(same) - 1, int(f * (len(same) - 1) + 0.5))]
    volume = f"{q(0.25)}–{q(0.75)}" if same else "a few"
    def expect(k):
        vals = sorted(c for i, c in enumerate(counts[:T]) if c and (T + k - i) % 7 == 0 and T + k - i <= 84)
        return vals[len(vals) // 2] if vals else 0
    y = record[-1]
    info = dict(p=p_today, issued=datetime.now(BTT).strftime("%d.%m.%Y, %H:%M BHUTAN TIME"), volume=volume,
                yesterday=y, outlook=outlook, record=record, accuracy=acc, brier=brier, baseline=baseline,
                live_days=sum(g["live"] for g in record), expect=[expect(k) for k in range(7)])
    for th in THEMES:
        render_weather(th, info, dates, counts)
    print(f"weights {w} · today {p_today:.0%} · accuracy {acc:.0%} (baseline {baseline:.0%}) · brier {brier:.3f}")


if __name__ == "__main__":
    main()
