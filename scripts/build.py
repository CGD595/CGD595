#!/usr/bin/env python3
"""Builds every static SVG in assets/{dark,light}/.

    pip install fonttools
    python3 scripts/build.py

Content lives at the top of this file; layout is computed from real font metrics.
"""
import random

from kit import EASE, THEMES, Doc, measure, sparkle, wrap

# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------
TAGLINE = ("Building AI systems for low-resource languages, sovereign architectures, "
           "and full-stack platforms — from Bhutan, for the world.")

MARQUEE = ["AI4Tarayana 1st place", "Aplos Lab co-founder", "Low-resource NLP", "BTN 500K pre-seed", "Bhutan",
           "Llama 3", "RAG systems", "Speech tech", "FastAPI", "Next.js", "Kotlin Multiplatform", "21Tech"]

STATS = [("7+", "Projects shipped"), ("500K", "BTN pre-seed"), ("4", "Bhutanese dialects"), ("~40%", "RAG retrieval gain")]

FEATURED = dict(
    no="01", title="108.BT", year="2026", link="108.bt",
    desc=("A place for anyone to stand among the 108 chortens raised at Gelephu Mindfulness City. "
          "Leave a photo and a prayer, sealed for the years you choose. Everything placed among "
          "the 108 is revealed together on 21 February 2027."),
    stack="Next.js · three.js · WebGL",
)

PROJECTS = [
    dict(slug="aplos", no="02", title="Aplos Lab", year="2025—26", link="aploslab.com",
         desc=("AI research startup building sovereign language tech: speech, translation and NLP "
               "for Dzongkha, Sharchop and Bumthap."),
         stack="NLP · TTS · Neural MT · Python"),
    dict(slug="zora", no="03", title="Zora AI", year="2024", link="live demo",
         desc="Personalized learning that generates videos, content and quizzes around how each student learns.",
         stack="Next.js · Node.js · Drizzle · Clerk"),
    dict(slug="druk", no="04", title="Druk Happy Cleaning", year="2026", link="live site",
         desc=("Full-stack service site for a Perth cleaning company. Quote and booking flow, "
               "before/after gallery, Google Reviews."),
         stack="Next.js · React · Tailwind"),
    dict(slug="zeebar", no="05", title="Zeebar Resort", year="2024", link="zeebarresort.bt",
         desc="Hotel booking with the RMA payment gateway, real-time availability and a guest-first UI.",
         stack="React · Node.js · Redux · JWT"),
]

PRIVATE = [
    ("Agentic RAG for investigators", "Best project 2026",
     "Reads handwritten case files through a 3-layer OCR pipeline, reasons across evidence with a multi-tool agent "
     "and points to the exact pixel behind every answer. Fully on-prem, zero cloud."),
    ("A national app, rebuilt", "Now",
     "Redesigning and rebuilding a Bhutan-focused app end to end on Kotlin Multiplatform, SwiftUI and Compose."),
    ("Camera-based smart parking", "Cohort build",
     "Real-time discovery, reservation and routing for a new city, built inside a national innovation cohort."),
    ("Handwritten Dzongkha OCR", "Research",
     "Crowdsourced dataset with intake, labelling, dedup and QA, plus an OCR model trained on the result."),
    ("On-chain wallet analytics", "Data",
     "Ethereum wallet tracking and behaviour analysis, processed at scale on Apache Spark."),
]

EXPERIENCE = [
    ("21Tech", "Software Engineer", "Bhutan", True),
    ("Aplos Lab", "Co-Founder & AI Researcher", "Bhutan", True),
    ("NoMindBhutan", "AI Engineer — agents & RAG for gov + enterprise", "Bhutan", False),
    ("Government agency", "Sole Developer — offline RAG, ~40% retrieval gain", "Thimphu", False),
    ("Druk Happy Cleaning", "Freelance Web Developer", "Perth · remote", False),
    ("Zeebar Resort", "Full-Stack Developer", "Samtse", False),
]

AWARDS = [
    ("2026", "Best Project of the Year", "CIT Gyalpozhing"),
    ("2026", "1st Place, AI4Tarayana Challenge", "Dialect translation + TTS"),
    ("2026", "Top 6 & BTN 500K pre-seed", "Bhutan Startup Launchpad"),
    ("2025", "Pelsung Cohort 2", "Gelephu Mindfulness City"),
]

STACK = [
    ("AI / ML", ["Python", "LangGraph", "Llama 3 · Qwen2.5", "Qdrant · ChromaDB", "TrOCR · docTR", "Text2SQL"]),
    ("Web", ["TypeScript", "Next.js · React", "Node.js · FastAPI", "PostgreSQL · Drizzle", "three.js", "Tailwind"]),
    ("Mobile", ["Kotlin Multiplatform", "Jetpack Compose", "SwiftUI", "Swift · Kotlin"]),
    ("Data & design", ["Apache Spark", "Computer vision", "Figma", "UX research"]),
]

SECTIONS = {
    "work": ("01", "Selected work", "Things I've built.", "Public · click to open"),
    "private": ("02", "Private work", "Described, not named.", "Client & NDA work"),
    "experience": ("03", "Experience", "Where I've worked.", ""),
    "awards": ("04", "Awards & recognition", "Built to win.", ""),
    "stack": ("05", "Skills & tools", "What I reach for.", ""),
    "cadence": ("01", "Activity", "Shipping cadence.", "Redrawn daily"),
}

W = 1200
built = []


def out(doc, name, theme):
    built.append((theme, name, doc.save(name, theme)))


def frame(doc, r=20):
    t = doc.t
    return f'<rect x=".5" y=".5" width="{doc.w-1}" height="{doc.h-1}" rx="{r}" fill="{t["card"]}" stroke="{t["border"]}"/>'


def sweep_layer(doc, gid, h, delay):
    t = doc.t
    doc.defs.append(
        f'<linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{t["primary"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["primary"]}" stop-opacity="{t["sweep_op"]}"/>'
        f'<stop offset="1" stop-color="{t["primary"]}" stop-opacity="0"/></linearGradient>'
    )
    return f'<rect class="sweep" style="animation-delay:{delay}s" x="0" y="0" width="240" height="{h}" fill="url(#{gid})"/>'


ROW_CSS = f".r{{animation:r .7s {EASE} both}}@keyframes r{{from{{opacity:0;transform:translateY(8px)}}}}"
DOT_CSS = ".dot{animation:dot 2.4s ease-in-out infinite}@keyframes dot{0%,100%{opacity:1}50%{opacity:.3}}"


# --------------------------------------------------------------------------
# hero
# --------------------------------------------------------------------------
def hero(theme):
    H = 600
    d = Doc(W, H, theme, "Chime Gyeltshen Dorji — AI-focused full-stack engineer, Bhutan")
    t = d.t
    d.css = f"""
.blind{{animation:breathe ease-in-out infinite}}
@keyframes breathe{{0%,100%{{opacity:.25}}50%{{opacity:.75}}}}
.aurora{{transform-box:fill-box;transform-origin:center;animation:aur 10s ease-in-out infinite}}
@keyframes aur{{0%,100%{{transform:scale(1);opacity:.8}}50%{{transform:scale(1.04);opacity:1}}}}
.line{{animation:up .95s {EASE} both}}
@keyframes up{{from{{transform:translateY(150px)}}to{{transform:none}}}}
.fade{{animation:fade .6s {EASE} both}}
@keyframes fade{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.bob{{animation:bob 2s ease-in-out infinite}}
@keyframes bob{{0%,100%{{transform:none}}50%{{transform:translateY(5px)}}}}
{DOT_CSS}
"""
    d.defs.append(
        f'<radialGradient id="au" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{t["aurora"]}" stop-opacity="{t["aurora_op"]}"/>'
        f'<stop offset=".6" stop-color="{t["aurora"]}" stop-opacity="{t["aurora_op"]*0.4:.3f}"/><stop offset="1" stop-color="{t["aurora"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="bl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["blind"]}" stop-opacity="0"/>'
        f'<stop offset=".4" stop-color="{t["blind"]}" stop-opacity="{t["blind_op"]}"/><stop offset=".6" stop-color="{t["blind"]}" stop-opacity="{t["blind_op"]}"/>'
        f'<stop offset="1" stop-color="{t["blind"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="fr"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
    )
    d.add(f'<g clip-path="url(#fr)"><rect width="{W}" height="{H}" fill="{t["bg"]}"/>')
    d.add(f'<ellipse class="aurora" cx="930" cy="110" rx="560" ry="470" fill="url(#au)"/>')
    for i in range(12):
        dur = 3.5 + (i % 4) * 0.9
        d.add(f'<rect class="blind" x="{i*100}" y="0" width="100" height="{H}" fill="url(#bl)" opacity=".5" '
              f'style="animation-duration:{dur:.1f}s;animation-delay:{i*0.28:.2f}s"/>')
    d.add(sweep_layer(d, "sw", H, 1.5))

    x0 = 64
    d.add(f'<g class="fade" style="animation-delay:.1s"><circle class="dot" cx="{x0+4}" cy="107" r="4" fill="{t["primary"]}"/>')
    d.add(d.text(x0 + 20, 112, "KUZU ZANGPO · BHUTAN · AI-FOCUSED FULL-STACK ENGINEER", "m", 15, t["muted"], 0.18) + "</g>")

    track = -0.045
    size = min(150, 690 / measure("GYELTSHEN", "h", 1, track))
    top = 150
    for i, word in enumerate(["CHIME", "GYELTSHEN", "DORJI"]):
        base = top + 0.74 * size + i * 0.86 * size
        cid = f"l{i}"
        d.defs.append(f'<clipPath id="{cid}"><rect x="0" y="{base-0.8*size:.1f}" width="800" height="{0.86*size:.1f}"/></clipPath>')
        d.add(f'<g clip-path="url(#{cid})"><g class="line" style="animation-delay:{0.28+i*0.13:.2f}s">'
              + d.text(x0 - 4, base, word, "h", round(size, 1), t["fg"], track) + "</g></g>")
    name_bottom = top + 0.74 * size + 2 * 0.86 * size

    cx, cw = 812, 324
    lines = wrap(TAGLINE, cw, "b", 19)
    y = name_bottom - 70 - (len(lines) - 1) * 30
    d.add('<g class="fade" style="animation-delay:.9s">')
    for ln in lines:
        d.add(d.text(cx, y, ln, "b", 19, t["muted"]))
        y += 30
    d.add(d.text(cx, name_bottom, "CHIMEGD.XYZ ↗", "m", 14, t["fg"], 0.2))
    d.add("</g>")

    d.add('<g class="fade" style="animation-delay:1.2s">')
    d.add(d.text(x0, H - 40, "AI-FOCUSED FULL-STACK ENGINEER", "m", 12.5, t["faint"], 0.2))
    d.add('<g class="bob">' + d.text(W - 64, H - 40, "SCROLL ↓", "m", 12.5, t["faint"], 0.2, anchor="end") + "</g></g>")
    d.add("</g>")
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="{t["border"]}"/>')
    out(d, "hero.svg", theme)


# --------------------------------------------------------------------------
# marquee
# --------------------------------------------------------------------------
def marquee(theme):
    H = 64
    d = Doc(W, H, theme, " · ".join(MARQUEE))
    t = d.t
    size, track = 13, 0.22
    items, x = [], 0.0
    for it in MARQUEE:
        s = it.upper()
        items.append(d.text(x, 37, s, "m", size, t["muted"], track))
        x += measure(s, "m", size, track) + 26
        items.append(sparkle(round(x, 1), 32, 6, t["primary"]))
        x += 32
    setw = x
    d.css = f".track{{animation:mq {setw/32:.1f}s linear infinite}}@keyframes mq{{to{{transform:translateX(-{setw:.1f}px)}}}}"
    d.defs.append(
        f'<linearGradient id="fl"><stop offset="0" stop-color="{t["bg"]}"/><stop offset="1" stop-color="{t["bg"]}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="fr" x1="1" x2="0"><stop offset="0" stop-color="{t["bg"]}"/><stop offset="1" stop-color="{t["bg"]}" stop-opacity="0"/></linearGradient>'
    )
    d.add(f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/><rect width="{W}" height="{H}" fill="{t["card"]}" opacity=".6"/>')
    d.add(f'<path d="M0 .5H{W}M0 {H-.5}H{W}" stroke="{t["border"]}"/>')
    d.add(f'<g transform="translate(40 0)"><g class="track">{"".join(items)}'
          f'<g transform="translate({setw:.1f} 0)">{"".join(items)}</g></g></g>')
    d.add(f'<rect width="90" height="{H-2}" y="1" fill="url(#fl)"/><rect x="{W-90}" width="90" height="{H-2}" y="1" fill="url(#fr)"/>')
    out(d, "marquee.svg", theme)


# --------------------------------------------------------------------------
# pills (each is a real link in the README)
# --------------------------------------------------------------------------
def pill(theme, slug, label, filled):
    size, pad, H = 17, 30, 52
    Wp = round(measure(label, "m", size) + pad * 2)
    d = Doc(Wp, H, theme, label)
    t = d.t
    if filled:
        d.add(f'<rect width="{Wp}" height="{H}" rx="{H/2}" fill="{t["primary"]}"/>')
        d.add(d.text(pad, 33, label, "m", size, t["on_primary"]))
    else:
        d.add(f'<rect x=".75" y=".75" width="{Wp-1.5}" height="{H-1.5}" rx="{(H-1.5)/2}" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>')
        d.add(d.text(pad, 33, label, "m", size, t["fg"]))
    out(d, f"pill-{slug}.svg", theme)


# --------------------------------------------------------------------------
# section heading:   01 / LABEL   then   Big phrase.
# --------------------------------------------------------------------------
def heading(theme, key):
    _, _, phrase, meta = SECTIONS[key]
    H = 104
    d = Doc(W, H, theme, phrase)
    t = d.t
    d.css = f".rule{{transform-origin:0 0;animation:rule 1.4s {EASE} both}}@keyframes rule{{from{{transform:scaleX(0)}}}}"
    body, dot = (phrase[:-1], ".") if phrase.endswith(".") else (phrase, "")
    d.add(d.tspan_text(0, 70, [(body, t["fg"], None), (dot, t["primary"], None)], "h", 62, -0.03))
    if meta:
        d.add(d.text(W - 4, 66, meta.upper(), "m", 13, t["muted"], 0.16, anchor="end"))
    d.add(f'<rect class="rule" x="4" y="{H-2}" width="{W-8}" height="1" fill="{t["border"]}"/>')
    out(d, f"h-{key}.svg", theme)


# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------
def stats(theme):
    H = 170
    d = Doc(W, H, theme, ", ".join(f"{v} {l}" for v, l in STATS))
    t = d.t
    d.css = f".s{{animation:s .8s {EASE} both}}@keyframes s{{from{{opacity:0;transform:translateY(12px)}}}}"
    d.add(frame(d))
    cw = W / len(STATS)
    for i, (v, label) in enumerate(STATS):
        x = i * cw
        if i:
            d.add(f'<path d="M{x:.1f} 28V{H-28}" stroke="{t["border"]}"/>')
        d.add(f'<g class="s" style="animation-delay:{i*0.1:.1f}s">')
        d.add(d.text(x + 36, 96, v, "h", 64, t["fg"], -0.04))
        d.add(d.text(x + 38, 134, label.upper(), "m", 14, t["muted"], 0.14))
        d.add("</g>")
    out(d, "stats.svg", theme)


# --------------------------------------------------------------------------
# project cards
# --------------------------------------------------------------------------
def arrow_badge(d, x, y, label):
    """right-aligned 'label (↗)' ending at x, baseline y"""
    t = d.t
    return (d.text(x - 50, y, label.upper(), "m", 12.5, t["muted"], 0.12, anchor="end")
            + f'<circle cx="{x-18}" cy="{y-4.5}" r="18" fill="none" stroke="{t["border"]}"/>'
            + d.text(x - 18, y + 0.5, "↗", "m", 17, t["primary"], anchor="middle"))


def chorten(x, y, s=1.0):
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({s})">'
            '<rect x="-1" y="0" width="2" height="6"/><rect x="-4" y="6" width="8" height="3"/>'
            '<rect x="-7" y="9" width="14" height="10" rx="1"/><rect x="-9" y="19" width="18" height="3"/>'
            '<rect x="-10.5" y="22" width="21" height="3"/></g>')


def featured(theme):
    p = FEATURED
    H = 420
    d = Doc(W, H, theme, f"{p['title']} — {p['desc']}")
    t = d.t
    rng = random.Random(108)
    d.css = f"""
.c{{fill:{t['primary']};animation:lit .5s ease-out both}}
@keyframes lit{{from{{fill:{t['off']}}}to{{fill:{t['primary']}}}}}
.cap{{animation:cap .8s {EASE} both;animation-delay:6.6s}}
@keyframes cap{{from{{opacity:0;transform:translateY(6px)}}}}
"""
    d.defs.append(f'<clipPath id="cc"><rect width="{W}" height="{H}" rx="20"/></clipPath>')
    d.add(frame(d))
    d.add(f'<g clip-path="url(#cc)">{sweep_layer(d, "sw", H, 2)}</g>')
    x = 44
    d.add(d.tspan_text(x, 62, [(p["no"], t["primary"], None), ("  —  FEATURED · " + p["year"], t["muted"], None)], "m", 14, 0.18))
    d.add(d.text(x - 3, 152, p["title"], "h", 84, t["fg"], -0.04))
    yy = 204
    for ln in wrap(p["desc"], 560, "b", 19):
        d.add(d.text(x, yy, ln, "b", 19, t["muted"]))
        yy += 30
    d.add(f'<path d="M{x} {H-84}H{640}" stroke="{t["border"]}"/>')
    d.add(d.text(x, H - 46, p["stack"].upper(), "m", 13, t["muted"], 0.12))
    d.add(arrow_badge(d, 640, H - 46, p["link"]))

    # 108 chortens, lit in a random order, like offerings being placed
    cols, rows, gx, gy = 12, 9, 37, 30
    ox, oy = W - 54 - (cols - 1) * gx, 70
    order = list(range(cols * rows))
    rng.shuffle(order)
    rank = {k: i for i, k in enumerate(order)}
    for r in range(rows):
        for c in range(cols):
            k = r * cols + c
            d.add(f'<g class="c" style="animation-delay:{0.4 + rank[k]*0.055:.2f}s">{chorten(ox + c*gx, oy + r*gy, 0.9)}</g>')
    d.add('<g class="cap">' + d.text(W - 44, H - 46, "108 / 108 · REVEALED 21.02.2027", "m", 12.5, t["muted"], 0.14, anchor="end") + "</g>")
    out(d, "featured.svg", theme)


def card(theme, p, i):
    Wc, H = 590, 330
    d = Doc(Wc, H, theme, f"{p['title']} — {p['desc']}")
    t = d.t
    d.defs.append(f'<clipPath id="cc"><rect width="{Wc}" height="{H}" rx="18"/></clipPath>')
    d.add(f'<rect x=".5" y=".5" width="{Wc-1}" height="{H-1}" rx="18" fill="{t["card"]}" stroke="{t["border"]}"/>')
    d.add(f'<g clip-path="url(#cc)">{sweep_layer(d, "sw", H, 3 + i * 1.1)}</g>')
    x = 34
    d.add(d.text(x, 56, p["no"], "m", 14, t["primary"], 0.18))
    d.add(d.text(Wc - 34, 56, p["year"], "m", 14, t["muted"], 0.18, anchor="end"))
    title = p["title"].upper()
    ts = 34 if measure(title, "h", 34, -0.03) < Wc - 68 else 28
    d.add(d.text(x - 2, 116, title, "h", ts, t["fg"], -0.03))
    y = 158
    for ln in wrap(p["desc"], Wc - 70, "b", 18.5)[:4]:
        d.add(d.text(x, y, ln, "b", 18.5, t["muted"]))
        y += 29
    d.add(f'<path d="M{x} {H-76}H{Wc-34}" stroke="{t["border"]}"/>')
    d.add(d.text(x, H - 38, p["stack"].upper(), "m", 13, t["muted"], 0.1))
    d.add(arrow_badge(d, Wc - 34, H - 38, p["link"]))
    out(d, f"card-{p['slug']}.svg", theme)


# --------------------------------------------------------------------------
# lists
# --------------------------------------------------------------------------
def lock(x, y, c):
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{c}" stroke-width="1.6">'
            '<rect x="0" y="7" width="14" height="11" rx="2.5"/><path d="M3 7V4.5a4 4 0 0 1 8 0V7"/></g>')


def private(theme):
    RH, top = 118, 8
    H = top + RH * len(PRIVATE) + 8
    d = Doc(W, H, theme, "Private work: " + "; ".join(p[0] for p in PRIVATE))
    t = d.t
    d.css = ROW_CSS
    d.add(frame(d))
    for i, (title, tag, desc) in enumerate(PRIVATE):
        y = top + i * RH
        if i:
            d.add(f'<path d="M36 {y}H{W-36}" stroke="{t["border"]}"/>')
        d.add(f'<g class="r" style="animation-delay:{0.1+i*0.08:.2f}s">')
        d.add(lock(38, y + 30, t["primary"]))
        d.add(d.text(72, y + 47, title, "h", 24, t["fg"], -0.02))
        for j, ln in enumerate(wrap(desc, 820, "b", 17)[:2]):
            d.add(d.text(72, y + 76 + j * 25, ln, "b", 17, t["muted"]))
        tg = tag.upper()
        tw = measure(tg, "m", 12, 0.16) + 28
        hl = tag in ("Now", "Best project 2026")
        stroke = t["primary"] if hl else t["border"]
        fill = f'fill="{t["primary"]}" fill-opacity=".1"' if hl else 'fill="none"'
        d.add(f'<rect x="{W-36-tw:.1f}" y="{y+28}" width="{tw:.1f}" height="28" rx="14" {fill} stroke="{stroke}"/>')
        d.add(d.text(W - 36 - tw / 2, y + 46.5, tg, "m", 12, t["primary"] if hl else t["muted"], 0.16, anchor="middle"))
        d.add("</g>")
    out(d, "private.svg", theme)


def experience(theme):
    RH = 84
    H = RH * len(EXPERIENCE) + 16
    d = Doc(W, H, theme, "Experience: " + "; ".join(f"{r} at {o}" for o, r, _, _ in EXPERIENCE))
    t = d.t
    d.css = ROW_CSS + DOT_CSS
    d.add(frame(d))
    for i, (org, role, loc, now) in enumerate(EXPERIENCE):
        y = 8 + i * RH
        if i:
            d.add(f'<path d="M36 {y}H{W-36}" stroke="{t["border"]}"/>')
        d.add(f'<g class="r" style="animation-delay:{0.1+i*0.08:.2f}s">')
        d.add(d.text(36, y + 52, f"{i+1:02d}", "m", 13, t["faint"], 0.16))
        d.add(d.text(90, y + 53, org, "h", 26, t["fg"], -0.025))
        ow = measure(org, "h", 26, -0.025)
        d.add(d.text(90 + ow + 18, y + 52, role, "b", 18, t["muted"]))
        if now:
            d.add(f'<circle class="dot" cx="{W-128}" cy="{y+47.5}" r="4" fill="{t["primary"]}"/>')
            d.add(d.text(W - 36, y + 52, "CURRENT", "m", 12.5, t["primary"], 0.16, anchor="end"))
        else:
            d.add(d.text(W - 36, y + 52, loc.upper(), "m", 12.5, t["muted"], 0.16, anchor="end"))
        d.add("</g>")
    out(d, "experience.svg", theme)


def awards(theme):
    RH = 84
    H = RH * len(AWARDS) + 16
    d = Doc(W, H, theme, "Awards: " + "; ".join(a[1] for a in AWARDS))
    t = d.t
    d.css = ROW_CSS
    d.add(frame(d))
    for i, (yr, title, org) in enumerate(AWARDS):
        y = 8 + i * RH
        if i:
            d.add(f'<path d="M36 {y}H{W-36}" stroke="{t["border"]}"/>')
        d.add(f'<g class="r" style="animation-delay:{0.1+i*0.08:.2f}s">')
        d.add(sparkle(44, y + 45, 8, t["primary"]))
        d.add(d.text(72, y + 53, title, "h", 26, t["fg"], -0.025))
        d.add(d.text(W - 110, y + 52, org.upper(), "m", 12.5, t["muted"], 0.16, anchor="end"))
        d.add(d.text(W - 36, y + 52, yr, "m", 14, t["fg"], 0.12, anchor="end"))
        d.add("</g>")
    out(d, "awards.svg", theme)


def stack(theme):
    rows = max(len(items) for _, items in STACK)
    H = 92 + rows * 40 + 20
    d = Doc(W, H, theme, "Skills: " + "; ".join(f"{g}: {', '.join(i)}" for g, i in STACK))
    t = d.t
    d.css = ROW_CSS
    d.add(frame(d))
    cw = (W - 72) / len(STACK)
    for gi, (group, items) in enumerate(STACK):
        x = 36 + gi * cw + (0 if gi == 0 else 26)
        if gi:
            d.add(f'<path d="M{36+gi*cw:.1f} 32V{H-32}" stroke="{t["border"]}"/>')
        d.add(d.tspan_text(x, 64, [(f"{gi+1:02d}", t["primary"], None), ("  " + group.upper(), t["muted"], None)], "m", 13, 0.16))
        for j, it in enumerate(items):
            d.add(f'<g class="r" style="animation-delay:{0.15+gi*0.08+j*0.05:.2f}s">'
                  + d.text(x, 112 + j * 40, it, "h", 21, t["fg"], -0.02) + "</g>")
    out(d, "stack.svg", theme)


def contact(theme):
    H = 300
    d = Doc(W, H, theme, "Let's build something. From Bhutan, for the world.")
    t = d.t
    d.defs.append(
        f'<radialGradient id="au" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{t["aurora"]}" stop-opacity="{t["aurora_op"]}"/>'
        f'<stop offset="1" stop-color="{t["aurora"]}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="cc"><rect width="{W}" height="{H}" rx="20"/></clipPath>'
    )
    d.add(f'<g clip-path="url(#cc)"><rect width="{W}" height="{H}" fill="{t["bg"]}"/>'
          f'<ellipse cx="{W/2}" cy="{H+60}" rx="620" ry="260" fill="url(#au)"/></g>')
    d.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="{t["border"]}"/>')
    lab = "07  /  CONTACT"
    d.add(d.tspan_text(W / 2 - measure(lab, "m", 14, 0.18) / 2, 76,
                       [("07", t["primary"], None), ("  /  CONTACT", t["muted"], None)], "m", 14, 0.18))
    phrase = "Let's build something"
    pw = measure(phrase + ".", "h", 76, -0.04)
    d.add(d.tspan_text(W / 2 - pw / 2, 160, [(phrase, t["fg"], None), (".", t["primary"], None)], "h", 76, -0.04))
    d.add(d.text(W / 2, 212, "From Bhutan, for the world.", "b", 19, t["muted"], anchor="middle"))
    d.add(d.text(W / 2, H - 34, "© 2026 CHIME GYELTSHEN DORJI · BHUTAN", "m", 12, t["faint"], 0.18, anchor="middle"))
    out(d, "contact.svg", theme)


if __name__ == "__main__":
    for th in THEMES:
        heading(th, "cadence")
    total = sum(s for _, _, s in built)
    print(f"built {len(built)} files, {total/1024:.0f}KB total")
