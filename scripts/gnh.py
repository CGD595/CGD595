#!/usr/bin/env python3
"""Gross Developer Happiness: Bhutan's Gross National Happiness method,
applied to one developer's last 12 months on GitHub.

Like the GNH survey, there are nine equally weighted domains, each with a
sufficiency threshold. Your score is the share of domains where you are
sufficient, and the bands use the survey's cutoffs:
  < 50% unhappy · 50-65% narrowly happy · 66-76% extensively happy · >= 77% deeply happy

Rhythm domains use the full contribution calendar (private work included as
counts); the rest use public repos and public commits only.

    GITHUB_TOKEN=... python3 scripts/gnh.py [login]
"""
import json
import math
import os
import re
import statistics
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

from kit import EASE, THEMES, Doc, measure

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "CGD595"
BTT = timezone(timedelta(hours=6))  # Bhutan Time


def gql(query, **vars_):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": vars_}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "gnh-svg"},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]


def collect():
    since = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    u = gql("""query($l:String!){user(login:$l){id
      contributionsCollection{
        contributionCalendar{weeks{contributionDays{contributionCount date weekday}}}
        totalIssueContributions totalPullRequestContributions totalPullRequestReviewContributions
        totalRepositoryContributions
        commitContributionsByRepository(maxRepositories:100){repository{name owner{login} isPrivate isFork}}}
      repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100){nodes{
        isFork stargazerCount forkCount createdAt primaryLanguage{name}
        languages(first:10){nodes{name}}}}}}""", l=LOGIN)["user"]
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]

    commits = []
    for r in cc["commitContributionsByRepository"]:
        repo = r["repository"]
        if repo["isPrivate"]:
            continue
        cursor = None
        for _ in range(10):
            h = gql("""query($o:String!,$n:String!,$id:ID!,$s:GitTimestamp!,$c:String){repository(owner:$o,name:$n){
              defaultBranchRef{target{...on Commit{history(first:100,after:$c,since:$s,author:{id:$id}){
              pageInfo{hasNextPage endCursor} nodes{authoredDate additions deletions messageHeadline}}}}}}}""",
                    o=repo["owner"]["login"], n=repo["name"], id=u["id"], s=since, c=cursor)
            ref = (h["repository"] or {}).get("defaultBranchRef")
            if not ref:
                break
            hist = ref["target"]["history"]
            commits += hist["nodes"]
            if not hist["pageInfo"]["hasNextPage"]:
                break
            cursor = hist["pageInfo"]["endCursor"]
    return u, cc, days, commits


GENERIC = re.compile(r"^(update|fix|wip|changes?|commit|test|misc|stuff|minor|edit|add files?)\b[\w./ -]{0,24}$", re.I)


def domains(u, cc, days, commits):
    counts = [d["contributionCount"] for d in days]
    weeks = [counts[i:i + 7] for i in range(0, len(counts) - 6, 7)]
    active_weeks = [sum(w) for w in weeks if sum(w)]
    med = statistics.median(active_weeks) if active_weeks else 0
    crunch_free = sum(1 for w in weeks if sum(w) <= 2.5 * med) / len(weeks) if weeks and med else 1
    windows = [counts[i:i + 7] for i in range(len(counts) - 6)]
    rested = sum(1 for w in windows if 0 in w) / len(windows)
    # weekends: Saturday(6) + Sunday(0) pairs
    wk = {}
    for d in days:
        if d["weekday"] in (0, 6):
            day = date.fromisoformat(d["date"])
            key = day if d["weekday"] == 6 else day - timedelta(days=1)
            wk.setdefault(key, []).append(d["contributionCount"])
    weekends_off = sum(1 for v in wk.values() if 0 in v) / max(1, len(wk))

    repos = [r for r in u["repositories"]["nodes"] if not r["isFork"]]
    new_repos = cc["totalRepositoryContributions"]
    langs = {n["name"] for r in repos for n in r["languages"]["nodes"]}
    community = cc["totalIssueContributions"] + cc["totalPullRequestContributions"] + cc["totalPullRequestReviewContributions"]
    msgs = [c["messageHeadline"].strip() for c in commits]
    good = sum(1 for m in msgs if len(m.split()) >= 3 and not GENERIC.match(m)) / max(1, len(msgs))
    adds = sum(c["additions"] for c in commits)
    dels = sum(c["deletions"] for c in commits)
    ecology = dels / adds if adds else 0
    stars = sum(r["stargazerCount"] + r["forkCount"] for r in repos)
    late = sum(1 for c in commits
               if datetime.fromisoformat(c["authoredDate"].replace("Z", "+00:00")).astimezone(BTT).hour < 5) / max(1, len(commits))

    pct = lambda x: f"{round(x*100)}%"
    # (domain, raw, target, higher_is_better, indicator text)
    return [
        ("Psychological wellbeing", crunch_free, 0.85, f"{pct(crunch_free)} of weeks without a crunch spike"),
        ("Health", rested, 0.70, f"{pct(rested)} of any 7 days include a rest day"),
        ("Time use", weekends_off, 0.60, f"{pct(weekends_off)} of weekends with a day off"),
        ("Education", new_repos, 3, f"{new_repos} new repos started this year"),
        ("Cultural diversity", len(langs), 4, f"{len(langs)} languages across public repos"),
        ("Community vitality", community, 12, f"{community} PRs, reviews & issues for others"),
        ("Good governance", good, 0.70, f"{pct(good)} of public commit messages say what changed"),
        ("Ecological diversity", ecology, 0.25, f"{pct(ecology)} as many lines deleted as added"),
        ("Living standards", stars, 10, f"{stars} stars & forks on public work"),
    ], dict(late=late, commits=len(commits), private=sum(counts))


SHORT = {"Psychological wellbeing": "WELLBEING", "Health": "HEALTH", "Time use": "TIME USE", "Education": "EDUCATION",
         "Cultural diversity": "CULTURE", "Community vitality": "COMMUNITY", "Good governance": "GOVERNANCE",
         "Ecological diversity": "ECOLOGY", "Living standards": "LIVING STD."}
BANDS = [(0.77, "Deeply happy"), (0.66, "Extensively happy"), (0.50, "Narrowly happy"), (0.0, "Unhappy")]


def render(theme, rows):
    W, H = 1200, 640
    d = Doc(W, H, theme, "Gross Developer Happiness")
    t = d.t
    suff = [raw >= target for _, raw, target, _ in rows]
    share = sum(suff) / len(rows)
    band = next(name for cut, name in BANDS if share >= cut)
    d.css = f"""
.petal{{transform-origin:330px 330px;animation:bloom 1.2s {EASE} both}}
@keyframes bloom{{from{{transform:scale(.2);opacity:0}}}}
.ring{{animation:ring 2s {EASE} both}}@keyframes ring{{from{{opacity:0}}}}
.r{{animation:r .6s {EASE} both}}@keyframes r{{from{{opacity:0;transform:translateX(8px)}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pl 3s ease-in-out infinite}}
@keyframes pl{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
"""
    d.defs.append(
        f'<radialGradient id="pg" cx="330" cy="330" r="215" gradientUnits="userSpaceOnUse">'
        f'<stop offset=".2" stop-color="{t["primary"]}" stop-opacity=".25"/><stop offset="1" stop-color="{t["primary"]}" stop-opacity=".95"/></radialGradient>'
    )
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="{t["card"]}" stroke="{t["border"]}"/>')

    cx, cy, r0, rt = 330, 330, 52, 180  # r0 core, rt = sufficiency ring
    n = len(rows)
    # guide rings
    for k, rr in enumerate((r0 + (rt - r0) * f for f in (0.33, 0.66))):
        d.add(f'<circle cx="{cx}" cy="{cy}" r="{rr:.1f}" fill="none" stroke="{t["border"]}"/>')
    for i, (name, raw, target, _) in enumerate(rows):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        score = min(raw / target, 1.25) if target else 0
        r = r0 + (rt - r0) * max(score, 0.06)
        half = math.pi / n * 0.62
        P = lambda a, rad: (cx + rad * math.cos(a), cy + rad * math.sin(a))
        b1, b2 = P(ang - half, r0), P(ang + half, r0)
        tip = P(ang, r)
        c1, c2 = P(ang - half * 1.7, r0 + (r - r0) * 0.45), P(ang - half * 0.18, r0 + (r - r0) * 0.9)
        c3, c4 = P(ang + half * 0.18, r0 + (r - r0) * 0.9), P(ang + half * 1.7, r0 + (r - r0) * 0.45)
        f2 = lambda p: f"{p[0]:.1f} {p[1]:.1f}"
        dpath = f"M{f2(b1)} C{f2(c1)} {f2(c2)} {f2(tip)} C{f2(c3)} {f2(c4)} {f2(b2)} Z"
        if suff[i]:
            style = f'fill="url(#pg)" stroke="{t["primary"]}" stroke-width="1.5"'
        else:
            style = f'fill="{t["muted"]}" fill-opacity=".10" stroke="{t["muted"]}" stroke-opacity=".7" stroke-width="1.5" stroke-dasharray="4 4"'
        d.add(f'<path class="petal" style="animation-delay:{0.15+i*0.09:.2f}s" d="{dpath}" {style}/>')
        # label outside the ring
        lr = rt + 62
        lx, ly = cx + lr * math.cos(ang), cy + lr * math.sin(ang)
        anchor = "middle" if abs(math.cos(ang)) < 0.3 else ("start" if math.cos(ang) > 0 else "end")
        label = SHORT[name]
        d.add(d.text(lx, ly + 4, label, "m", 11.5, t["primary"] if suff[i] else t["muted"], 0.14, anchor=anchor))
    d.add(f'<circle class="ring" cx="{cx}" cy="{cy}" r="{rt}" fill="none" stroke="{t["primary"]}" stroke-opacity=".55" stroke-dasharray="2 6"/>')
    d.add(f'<circle cx="{cx}" cy="{cy}" r="{r0-6}" fill="{t["bg"]}" stroke="{t["border"]}"/>')
    d.add(d.text(cx, cy + 8, f"{round(share*100)}%", "h", 30, t["fg"], -0.03, anchor="middle"))
    d.add(d.text(cx, cy + 26, f"{sum(suff)} / {n}", "m", 10.5, t["muted"], 0.14, anchor="middle"))

    x = 660
    d.add(d.tspan_text(x, 74, [("GROSS NATIONAL HAPPINESS", t["primary"], None), ("  ·  APPLIED TO MY COMMITS", t["muted"], None)], "m", 12.5, 0.16))
    d.add(d.tspan_text(x - 2, 128, [(band, t["fg"], None), (".", t["primary"], None)], "h", 46, -0.035))
    d.add(d.text(x, 160, f"Sufficient in {sum(suff)} of 9 domains, using the GNH survey's own cutoffs.", "b", 16, t["muted"]))
    y = 206
    for i, (name, raw, target, text) in enumerate(rows):
        d.add(f'<g class="r" style="animation-delay:{0.4+i*0.06:.2f}s">')
        if suff[i]:
            d.add(f'<circle cx="{x+6}" cy="{y-5}" r="5" fill="{t["primary"]}"/>')
        else:
            d.add(f'<circle cx="{x+6}" cy="{y-5}" r="4.5" fill="none" stroke="{t["muted"]}" stroke-width="1.5"/>')
        d.add(d.text(x + 24, y, name, "h", 15.5, t["fg"], -0.01))
        d.add(d.text(x + 24 + measure(name, "h", 15.5, -0.01) + 12, y, text, "b", 14.5, t["muted"]))
        d.add("</g>")
        y += 38
    d.add(d.text(x, H - 34, f"UPDATED {date.today():%d.%m.%Y} · RHYTHM FROM ALL WORK, THE REST FROM PUBLIC REPOS", "m", 10.5, t["faint"], 0.12))
    d.save("gnh.svg", theme)
    return share, band


if __name__ == "__main__":
    u, cc, days, commits = collect()
    rows, extra = domains(u, cc, days, commits)
    for name, raw, target, text in rows:
        print(f"  {'✓' if raw >= target else '·'} {name:24s} {text}")
    for th in THEMES:
        share, band = render(th, rows)
    print(f"GNH: {share:.0%} — {band}  ({extra['commits']} public commits read)")
