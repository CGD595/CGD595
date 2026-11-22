#!/usr/bin/env python3
"""Generates the static SVG artwork for the profile README.

Run:  python3 scripts/build.py      (writes into ./assets)
Everything is plain SVG + CSS animation, so it renders inside GitHub's <img>.
"""
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

# ---- tokens ---------------------------------------------------------------
BG = "#0A0E17"
PANEL = "#0F1522"
LINE = "#1E2738"
INK = "#EAEFF7"
MUTED = "#8A95A8"
DIM = "#5B6578"
# Lungta prayer flags: blue, white, red, green, yellow (sky, air, fire, water, earth)
FLAGS = ["#3E8BFF", "#E9EEF6", "#F0524F", "#2FBF71", "#F6B940"]
GOLD = "#F6B940"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace"

BASE_CSS = f"""
.sans{{font-family:{SANS}}}
.mono{{font-family:{MONO}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}.cover{{display:none}}.cycle text{{opacity:1}}.cycle text:not(:first-child){{display:none}}}}
"""


def svg(w, h, body, css="", label=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">\n'
        f"<style>{BASE_CSS}{css}</style>\n{body}\n</svg>\n"
    )


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")
    print("wrote", name, f"{len(content)/1024:.1f}KB")


def t(s):
    return escape(s)


def ridge_path(rng, w, base, amp, roughness, step=6):
    """Mountain silhouette from layered sines + jitter."""
    phases = [rng.uniform(0, math.tau) for _ in range(4)]
    freqs = [1.3, 2.9, 6.1, 13.7]
    weights = [1.0, 0.45, 0.22 * roughness, 0.1 * roughness]
    pts = []
    for x in range(0, w + step, step):
        u = x / w
        y = sum(wt * math.sin(u * f * math.tau + p) for wt, f, p in zip(weights, freqs, phases))
        y += rng.uniform(-0.05, 0.05) * roughness
        pts.append((x, base - amp * (0.5 + 0.5 * y / sum(weights))))
    return pts


def to_area(pts, h):
    d = f"M0 {h} " + " ".join(f"L{x:.1f} {y:.1f}" for x, y in pts) + f" L{pts[-1][0]:.1f} {h} Z"
    return d


def flag_string(x0, y0, x1, y1, sag, n, cls_prefix="f"):
    """Prayer flags hanging from a catenary-ish curve."""
    out = [f'<path d="M{x0} {y0} Q{(x0+x1)/2} {max(y0,y1)+sag*2} {x1} {y1}" '
           f'stroke="#C9D2E0" stroke-opacity=".55" stroke-width="1.2" fill="none"/>']
    for i in range(n):
        u = (i + 0.5) / n
        # quadratic bezier point
        cx, cy = (x0 + x1) / 2, max(y0, y1) + sag * 2
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u ** 2 * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u ** 2 * y1
        c = FLAGS[i % 5]
        delay = -(i * 0.37) % 3
        out.append(
            f'<g transform="translate({x:.1f} {y:.1f})"><g class="flag" style="animation-delay:{delay:.2f}s">'
            f'<rect x="-9" y="0" width="18" height="24" rx="1.5" fill="{c}" fill-opacity=".92"/>'
            f'<rect x="-5" y="6" width="10" height="10" rx="1" fill="#000" fill-opacity=".12"/>'
            f"</g></g>"
        )
    return "\n".join(out)


# ---- hero -----------------------------------------------------------------
def hero():
    W, H = 1200, 460
    rng = random.Random(21)
    stars = []
    for i in range(110):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.62)
        r = rng.choice([0.6, 0.8, 1.0, 1.3])
        d = rng.uniform(2.5, 6)
        dl = -rng.uniform(0, 6)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" class="tw" '
            f'style="animation-duration:{d:.1f}s;animation-delay:{dl:.1f}s"/>'
        )

    far = ridge_path(rng, W, 400, 120, 1.0)
    mid = ridge_path(rng, W, 430, 90, 1.3)
    near = ridge_path(rng, W, 458, 50, 1.6)

    # snow caps: clip the far ridge to its top band
    peak_y = min(y for _, y in far)
    snow_line = peak_y + 70

    css = """
.tw{animation:tw ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:.95}}
.flag{transform-box:fill-box;transform-origin:50% 0;animation:sway 3s ease-in-out infinite}
@keyframes sway{0%,100%{transform:rotate(-7deg) skewY(-3deg)}50%{transform:rotate(7deg) skewY(3deg)}}
.mist{animation:drift 38s linear infinite}
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(-1200px)}}
.rise{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.cycle text{animation:cyc 9s infinite both}
.cycle text:nth-child(2){animation-delay:3s}
.cycle text:nth-child(3){animation-delay:6s}
@keyframes cyc{0%{opacity:0;transform:translateY(8px)}4%,30%{opacity:1;transform:none}34%,100%{opacity:0;transform:translateY(-8px)}}
.moon{animation:glow 7s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:.75}50%{opacity:1}}
"""
    body = f"""
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05070D"/><stop offset=".55" stop-color="#0D1424"/><stop offset="1" stop-color="#1A1830"/>
  </linearGradient>
  <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{GOLD}" stop-opacity=".35"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="farG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2A3552"/><stop offset="1" stop-color="#151C2E"/>
  </linearGradient>
  <linearGradient id="midG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#182036"/><stop offset="1" stop-color="#0E1322"/>
  </linearGradient>
  <radialGradient id="mistG" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#A9BCE0" stop-opacity=".16"/><stop offset="1" stop-color="#A9BCE0" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="snowG" gradientUnits="userSpaceOnUse" x1="0" y1="{peak_y:.0f}" x2="0" y2="{snow_line:.0f}"><stop offset="0" stop-color="#EEF2F8" stop-opacity=".95"/><stop offset=".55" stop-color="#C9D4E8" stop-opacity=".35"/><stop offset="1" stop-color="#C9D4E8" stop-opacity="0"/></linearGradient>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{''.join(stars)}
<g class="moon"><circle cx="1050" cy="92" r="90" fill="url(#halo)"/>
<circle cx="1050" cy="92" r="26" fill="#F7E7C0"/><circle cx="1062" cy="84" r="24" fill="#0B1020"/></g>
<path d="{to_area(far, H)}" fill="url(#farG)"/>
<path d="{to_area(far, H)}" fill="url(#snowG)"/>
<g class="mist"><ellipse cx="150" cy="372" rx="260" ry="34" fill="url(#mistG)"/><ellipse cx="560" cy="360" rx="300" ry="34" fill="url(#mistG)"/><ellipse cx="980" cy="380" rx="280" ry="34" fill="url(#mistG)"/><ellipse cx="1350" cy="368" rx="260" ry="34" fill="url(#mistG)"/><ellipse cx="1760" cy="360" rx="300" ry="34" fill="url(#mistG)"/><ellipse cx="2180" cy="380" rx="280" ry="34" fill="url(#mistG)"/></g>
{flag_string(640, 30, 1210, 120, 60, 22)}
<path d="{to_area(mid, H)}" fill="url(#midG)"/>
<path d="{to_area(near, H)}" fill="{BG}"/>

<g class="sans">
  <text x="64" y="92" class="rise mono" style="animation-delay:.1s" font-size="14" letter-spacing="3" fill="{GOLD}">KUZU ZANGPO — HELLO FROM BHUTAN</text>
  <text x="62" y="160" class="rise" style="animation-delay:.25s" font-size="60" font-weight="800" letter-spacing="-1.5" fill="{INK}">Chime Gyeltshen Dorji</text>
  <text x="64" y="202" class="rise" style="animation-delay:.4s" font-size="22" fill="{MUTED}">AI engineer building sovereign language tech for the Himalayas.</text>
  <g class="rise" style="animation-delay:.55s">
    <text x="64" y="252" class="mono" font-size="17" fill="{DIM}">currently shipping →</text>
    <g class="cycle mono" font-size="17" font-weight="600">
      <text x="276" y="252" fill="{FLAGS[0]}">LLM agents &amp; agentic RAG</text>
      <text x="276" y="252" fill="{FLAGS[3]}">Dzongkha · Sharchop · Bumthap NLP</text>
      <text x="276" y="252" fill="{GOLD}">full-stack &amp; mobile at 21Tech</text>
    </g>
  </g>
</g>
</g>
"""
    write("hero.svg", svg(W, H, body, css, "Chime Gyeltshen Dorji — AI engineer from Bhutan"))


# ---- terminal ---------------------------------------------------------------
def terminal():
    W = 1200
    FS = 16
    CW = FS * 0.602  # monospace advance
    LH = 30
    x0 = 44
    y = 92
    lines = [
        ("cmd", "whoami"),
        ("out", [("chime gyeltshen dorji", INK), ("  ·  ai engineer  ·  ", DIM), ("bhutan", GOLD)]),
        ("cmd", "cat ./now"),
        ("out", [("software engineer ", INK), ("@21Tech", FLAGS[0]), ("   co-founder ", INK), ("@AplosLab", FLAGS[3])]),
        ("cmd", "ls ./wins"),
        ("out", [("1st  ai4tarayana-2026", GOLD), ("    best-project-of-the-year-2026", GOLD), ("    btn-500k-preseed", FLAGS[3])]),
        ("cmd", 'agent run "make dzongkha first-class on the internet"'),
        ("out", [("  ▸ plan      ", FLAGS[0]), ("corpus → ocr → translate → speak", MUTED)]),
        ("out", [("  ▸ retrieve  ", FLAGS[0]), ("bhutanese-dialect-corpus", MUTED)]),
        ("out", [("  ▸ build     ", FLAGS[0]), ("nmt · tts · handwritten-ocr", MUTED)]),
        ("out", [("  ✓ status    ", FLAGS[3]), ("in progress — follow along ↓", INK)]),
    ]
    H = y + LH * len(lines) + 40
    css = f"""
.cover{{animation-fill-mode:both;animation-timing-function:steps(var(--n));animation-name:type}}
@keyframes type{{from{{transform:translateX(0)}}to{{transform:translateX(var(--w))}}}}
.show{{animation:show .25s ease-out both}}
@keyframes show{{from{{opacity:0}}to{{opacity:1}}}}
.blink{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
"""
    parts = []
    tcur = 0.4
    for kind, content in lines:
        if kind == "cmd":
            parts.append(
                f'<text x="{x0}" y="{y}" class="mono show" style="animation-delay:{tcur:.2f}s" font-size="{FS}">'
                f'<tspan fill="{FLAGS[3]}">❯</tspan></text>'
            )
            cx = x0 + CW * 2
            parts.append(f'<text x="{cx:.1f}" y="{y}" class="mono" font-size="{FS}" fill="{INK}">{t(content)}</text>')
            n = len(content)
            w = n * CW + 4
            dur = max(0.35, n * 0.045)
            parts.append(
                f'<rect x="{cx-1:.1f}" y="{y-FS-2}" width="{w+2:.1f}" height="{FS+10}" fill="{PANEL}" class="cover" '
                f'style="--n:{n};--w:{w:.1f}px;animation-duration:{dur:.2f}s;animation-delay:{tcur+0.15:.2f}s"/>'
            )
            tcur += 0.15 + dur + 0.25
        else:
            spans = "".join(f'<tspan fill="{c}">{t(s)}</tspan>' for s, c in content)
            parts.append(
                f'<text x="{x0}" y="{y}" class="mono show" style="animation-delay:{tcur:.2f}s" '
                f'font-size="{FS}" xml:space="preserve">{spans}</text>'
            )
            tcur += 0.22
        y += LH
    parts.append(
        f'<g class="show" style="animation-delay:{tcur:.2f}s"><text x="{x0}" y="{y}" class="mono" font-size="{FS}" fill="{FLAGS[3]}">❯</text>'
        f'<rect x="{x0 + CW*2:.1f}" y="{y-FS+1}" width="{CW:.1f}" height="{FS+2}" fill="{INK}" class="blink"/></g>'
    )
    H = y + 34
    dots = "".join(
        f'<circle cx="{30+i*20}" cy="26" r="6" fill="{c}"/>' for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"])
    )
    body = f"""
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{PANEL}" stroke="{LINE}"/>
<path d="M.5 52 H{W-.5}" stroke="{LINE}"/>
{dots}
<text x="{W/2}" y="31" text-anchor="middle" class="mono" font-size="13" fill="{DIM}">cgd@druk — ~/aplos — zsh</text>
<g>{''.join(f'<rect x="{W-140+i*20}" y="20" width="14" height="12" rx="2" fill="{c}" fill-opacity=".85"/>' for i, c in enumerate(FLAGS))}</g>
{chr(10).join(parts)}
"""
    write("terminal.svg", svg(W, H, body, css, "Terminal: whoami — AI engineer at 21Tech and co-founder of Aplos Lab"))


# ---- section header -------------------------------------------------------
def header(slug, num, title, sub):
    W, H = 1200, 86
    stripe = "".join(
        f'<rect x="{i*14}" y="0" width="10" height="16" rx="1.5" fill="{c}" class="fl" style="animation-delay:{-i*0.3:.1f}s"/>'
        for i, c in enumerate(FLAGS)
    )
    css = """
.fl{transform-box:fill-box;transform-origin:50% 0;animation:sw 3.2s ease-in-out infinite}
@keyframes sw{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}
.grow{transform-origin:0 50%;animation:grow 1.4s cubic-bezier(.2,.7,.2,1) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
"""
    body = f"""
<g transform="translate(4 30)">{stripe}</g>
<text x="88" y="45" class="mono" font-size="14" letter-spacing="2" fill="{GOLD}">{t(num)}</text>
<text x="128" y="47" class="sans" font-size="30" font-weight="750" letter-spacing="-.5" fill="{INK}">{t(title)}</text>
<text x="128" y="72" class="sans" font-size="15" fill="{MUTED}">{t(sub)}</text>
<rect x="4" y="84" width="{W-8}" height="1" fill="{LINE}" class="grow"/>
"""
    # transparent bg; light text needs a dark host — pair with a dark-backed rect for light mode readers
    body = f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>' + body.replace('x="4" y="84"', 'x="20" y="84"').replace(
        'translate(4 30)', 'translate(24 30)')
    body = body.replace('x="88" y="45"', 'x="108" y="45"').replace('x="128" y="47"', 'x="148" y="47"').replace(
        'x="128" y="72"', 'x="148" y="72"')
    write(f"h-{slug}.svg", svg(W, H, body, css, title))


# ---- stat tiles -------------------------------------------------------------
def stats():
    W, H = 1200, 168
    tiles = [
        ("1st", "AI4Tarayana Challenge", "2026 · dialect translation + TTS", GOLD),
        ("Best", "Project of the Year", "2026 · CIT Gyalpozhing", FLAGS[0]),
        ("500K", "BTN pre-seed grant", "Bhutan Startup Launchpad · top 6", FLAGS[3]),
        ("3", "Bhutanese languages", "Dzongkha · Sharchop · Bumthap", FLAGS[2]),
    ]
    gap = 16
    tw = (W - gap * 3) / 4
    css = """
.tile{animation:up .8s cubic-bezier(.2,.7,.2,1) both}
@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.bar{transform-origin:0 0;animation:bar 1.2s .3s cubic-bezier(.2,.7,.2,1) both}
@keyframes bar{from{transform:scaleX(0)}to{transform:scaleX(1)}}
"""
    parts = []
    for i, (big, l1, l2, c) in enumerate(tiles):
        x = i * (tw + gap)
        parts.append(f"""<g transform="translate({x:.1f} 0)"><g class="tile" style="animation-delay:{i*0.12:.2f}s">
<rect x=".5" y=".5" width="{tw-1:.1f}" height="{H-1}" rx="14" fill="{PANEL}" stroke="{LINE}"/>
<rect x="20" y="0" width="{tw-40:.1f}" height="3" rx="1.5" fill="{c}" class="bar"/>
<text x="24" y="76" class="sans" font-size="48" font-weight="800" letter-spacing="-1.5" fill="{c}">{t(big)}</text>
<text x="24" y="110" class="sans" font-size="17" font-weight="650" fill="{INK}">{t(l1)}</text>
<text x="24" y="136" class="sans" font-size="13.5" fill="{MUTED}">{t(l2)}</text>
</g></g>""")
    write("stats.svg", svg(W, H, "\n".join(parts), css, "Awards: 1st AI4Tarayana 2026, Best Project 2026, BTN 500K pre-seed"))


# ---- project cards ----------------------------------------------------------
def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def card(slug, name, kicker, desc, tags, cta, color, badge=None):
    W, H = 590, 236
    lines = wrap(desc, 58)[:3]
    tx = 28
    chips = []
    for tag in tags:
        w = len(tag) * 7.4 + 22
        chips.append(
            f'<g transform="translate({tx:.1f} 182)"><rect width="{w:.1f}" height="28" rx="14" fill="{color}" fill-opacity=".10" stroke="{color}" stroke-opacity=".35"/>'
            f'<text x="{w/2:.1f}" y="18.5" text-anchor="middle" class="mono" font-size="12.5" fill="{color}">{t(tag)}</text></g>'
        )
        tx += w + 8
    css = """
.sheen{animation:sheen 6s ease-in-out infinite}
@keyframes sheen{0%,60%{transform:translateX(-700px)}100%{transform:translateX(700px)}}
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}
"""
    badge_svg = ""
    if badge:
        bw = len(badge) * 7.6 + 24
        badge_svg = (f'<g transform="translate({W-28-bw:.1f} 26)"><rect width="{bw:.1f}" height="26" rx="13" fill="{GOLD}" fill-opacity=".14"/>'
                     f'<text x="{bw/2:.1f}" y="17.5" text-anchor="middle" class="mono" font-size="12" font-weight="600" fill="{GOLD}">{t(badge)}</text></g>')
    body = f"""
<defs>
  <linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <radialGradient id="gl" cx="1" cy="0" r="1"><stop offset="0" stop-color="{color}" stop-opacity=".22"/><stop offset=".6" stop-color="{color}" stop-opacity="0"/></radialGradient>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{PANEL}"/>
<rect width="{W}" height="{H}" fill="url(#gl)"/>
<rect class="sheen" x="0" y="0" width="300" height="{H}" fill="url(#sh)"/>
<rect x="0" y="0" width="4" height="{H}" fill="{color}"/>
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{LINE}"/>
<text x="28" y="44" class="mono" font-size="12" letter-spacing="2" fill="{color}">{t(kicker.upper())}</text>
{badge_svg}
<text x="28" y="82" class="sans" font-size="27" font-weight="780" letter-spacing="-.5" fill="{INK}">{t(name)}</text>
{''.join(f'<text x="28" y="{112+i*22}" class="sans" font-size="15" fill="{MUTED}">{t(l)}</text>' for i, l in enumerate(lines))}
{''.join(chips)}
<g transform="translate({W-28} 202)"><circle cx="-8" cy="-6" r="4" fill="{color}" class="pulse"/></g>
<text x="{W-44}" y="201" text-anchor="end" class="mono" font-size="12.5" fill="{DIM}">{t(cta)}</text>
"""
    write(f"p-{slug}.svg", svg(W, H, body, css, f"{name} — {desc}"))


# ---- experience timeline ---------------------------------------------------
def timeline():
    W = 1200
    rows = [
        ("Software Engineer", "21Tech", "now", "Software, mobile & web systems for national and enterprise clients.", FLAGS[0]),
        ("Co-Founder & AI Researcher", "Aplos Lab", "now", "NLP + speech models for Dzongkha & Sharchop. Led the Bhutanese Dialect Corpus.", FLAGS[3]),
        ("AI Engineer", "NoMindBhutan", "", "Production AI agents and custom RAG architectures for government & enterprise.", GOLD),
        ("Sole Developer", "Anti-Corruption Commission", "", "Air-gapped RAG on Llama 3 + ChromaDB. ~40% retrieval efficiency gain.", FLAGS[2]),
        ("Full-Stack Developer", "Zeebar Resort · Druk Happy Cleaning", "", "Booking systems, RMA payment gateway, remote client work for Perth, AU.", FLAGS[1]),
    ]
    RH = 86
    H = 40 + RH * len(rows)
    css = """
.row{animation:in .7s cubic-bezier(.2,.7,.2,1) both}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
.spine{transform-origin:0 0;animation:spine 1.6s cubic-bezier(.2,.7,.2,1) both}
@keyframes spine{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.ping{transform-box:fill-box;transform-origin:center;animation:ping 2s ease-out infinite}
@keyframes ping{from{transform:scale(1);opacity:.6}to{transform:scale(2.6);opacity:0}}
"""
    parts = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{PANEL}" stroke="{LINE}"/>',
             f'<rect x="61" y="44" width="2" height="{RH*(len(rows)-1)}" fill="{LINE}" class="spine"/>']
    for i, (role, org, now, desc, c) in enumerate(rows):
        y = 44 + i * RH
        ping = f'<circle cx="62" cy="{y}" r="7" fill="{c}" class="ping"/>' if now else ""
        nowtag = ""
        if now:
            nowtag = (f'<rect x="{W-110}" y="{y-14}" width="70" height="24" rx="12" fill="{FLAGS[3]}" fill-opacity=".12"/>'
                      f'<text x="{W-75}" y="{y+2}" text-anchor="middle" class="mono" font-size="12" fill="{FLAGS[3]}">current</text>')
        parts.append(f"""<g class="row" style="animation-delay:{0.2+i*0.15:.2f}s">
{ping}<circle cx="62" cy="{y}" r="7" fill="{PANEL}" stroke="{c}" stroke-width="3"/>
<text x="96" y="{y+6}" class="sans" font-size="19" font-weight="700" fill="{INK}">{t(role)} <tspan fill="{DIM}" font-weight="400">at</tspan> <tspan fill="{c}">{t(org)}</tspan></text>
<text x="96" y="{y+32}" class="sans" font-size="15" fill="{MUTED}">{t(desc)}</text>
{nowtag}</g>""")
    write("experience.svg", svg(W, H, "\n".join(parts), css, "Experience timeline"))


# ---- stack ------------------------------------------------------------------
def stack():
    W = 1200
    groups = [
        ("AI / ML", FLAGS[0], ["Python", "LangGraph", "Llama 3", "ChromaDB", "RAG", "Text2SQL", "OCR", "Neural MT", "TTS", "VLMs"]),
        ("Web", FLAGS[3], ["TypeScript", "Next.js", "React", "Node.js", "FastAPI", "PostgreSQL", "Drizzle ORM", "Vercel"]),
        ("Mobile", GOLD, ["Kotlin Multiplatform", "Jetpack Compose", "SwiftUI", "Swift", "Kotlin"]),
        ("Also", FLAGS[2], ["Java", "JavaScript", "Computer Vision", "Supabase", "Docker"]),
    ]
    rowh = 58
    H = 28 + rowh * len(groups) + 10
    css = """
.chip{animation:pop .5s cubic-bezier(.3,1.4,.5,1) both}
@keyframes pop{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:none}}
"""
    parts = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{PANEL}" stroke="{LINE}"/>']
    k = 0
    for gi, (label, c, items) in enumerate(groups):
        y = 30 + gi * rowh
        parts.append(f'<text x="32" y="{y+20}" class="mono" font-size="13" letter-spacing="2" fill="{c}">{t(label.upper())}</text>')
        x = 160
        for it in items:
            w = len(it) * 8.1 + 30
            parts.append(
                f'<g transform="translate({x:.1f} {y})"><g class="chip" style="transform-origin:{w/2:.0f}px 15px;animation-delay:{k*0.035:.2f}s">'
                f'<rect width="{w:.1f}" height="32" rx="9" fill="#151C2B" stroke="{LINE}"/>'
                f'<circle cx="14" cy="16" r="3.5" fill="{c}"/>'
                f'<text x="25" y="21" class="sans" font-size="14" fill="{INK}">{t(it)}</text></g></g>'
            )
            x += w + 10
            k += 1
    write("stack.svg", svg(W, H, "\n".join(parts), css, "Tech stack"))


# ---- contact buttons -------------------------------------------------------
def button(slug, label, glyph, color):
    W, H = 220, 52
    css = """
.b{animation:b 3s ease-in-out infinite}
@keyframes b{0%,100%{stroke-opacity:.35}50%{stroke-opacity:.9}}
"""
    body = f"""
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="26" fill="{PANEL}" stroke="{color}" stroke-width="1.5" class="b"/>
<circle cx="28" cy="26" r="13" fill="{color}" fill-opacity=".15"/>
<text x="28" y="31" text-anchor="middle" class="mono" font-size="14" font-weight="700" fill="{color}">{t(glyph)}</text>
<text x="52" y="31.5" class="sans" font-size="15.5" font-weight="650" fill="{INK}">{t(label)}</text>
<text x="{W-24}" y="31" text-anchor="end" class="sans" font-size="15" fill="{DIM}">↗</text>
"""
    write(f"b-{slug}.svg", svg(W, H, body, css, label))


def footer():
    W, H = 1200, 150
    rng = random.Random(7)
    a = ridge_path(rng, W, 150, 90, 1.1)
    b = ridge_path(rng, W, 150, 55, 1.4)
    css = """
.fade{animation:f 1.2s .3s both}@keyframes f{from{opacity:0}to{opacity:1}}
.flag{transform-box:fill-box;transform-origin:50% 0;animation:sway 3s ease-in-out infinite}
@keyframes sway{0%,100%{transform:rotate(-7deg) skewY(-3deg)}50%{transform:rotate(7deg) skewY(3deg)}}
"""
    body = f"""
<defs><clipPath id="fr"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<linearGradient id="fg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070D"/><stop offset="1" stop-color="#121A2C"/></linearGradient></defs>
<g clip-path="url(#fr)">
<rect width="{W}" height="{H}" fill="url(#fg)"/>
{flag_string(-10, 20, 1210, 20, 22, 40)}
<path d="{to_area(a, H)}" fill="#1A2238"/>
<path d="{to_area(b, H)}" fill="{PANEL}"/>
<text x="{W/2}" y="116" text-anchor="middle" class="sans fade" font-size="24" font-weight="750" fill="{INK}">Tashi Delek <tspan fill="{GOLD}">·</tspan> <tspan fill="{MUTED}" font-weight="400">thanks for scrolling this far</tspan></text>
</g>
"""
    write("footer.svg", svg(W, H, body, css, "Tashi Delek"))


if __name__ == "__main__":
    hero()
    terminal()
    stats()
    header("work", "01", "Selected work", "Things I've built — click a card to open it")
    header("journey", "02", "Journey", "Where I've been shipping")
    header("stack", "03", "Toolkit", "What I reach for")
    header("ridge", "04", "Contribution Himalaya", "My last 12 months of commits, drawn as mountains — regenerated daily by a GitHub Action")
    card("aplos", "Aplos Lab", "Co-founded · Sovereign AI",
         "Speech, translation and NLP systems for Dzongkha, Sharchop and Bumthap, so Bhutanese languages work on the internet.",
         ["NLP", "TTS", "Neural MT", "Python"], "aploslab.com", FLAGS[3], "BTN 500K")
    card("acc", "ACC Document Intelligence", "Agentic RAG · air-gapped",
         "Reads handwritten investigative files via 3-layer OCR, a LangGraph multi-tool agent, Text2SQL cross-referencing and VLM answer highlighting. Zero cloud.",
         ["Llama 3", "LangGraph", "ChromaDB", "FastAPI"], "confidential", FLAGS[0], "BEST PROJECT 2026")
    card("tarayana", "Dialect Translator + TTS", "AI4Tarayana · 1st place",
         "Multilingual translation and text-to-speech platform for Bhutanese dialects, built for the AI4Tarayana Challenge.",
         ["Neural MT", "TTS", "Python"], "ai4tarayana 2026", GOLD, "1ST PLACE")
    card("zora", "Zora AI", "Personalized learning",
         "Generates custom videos, content and quizzes for every student, shaped around how they learn.",
         ["Next.js", "Node.js", "Drizzle", "Postgres"], "live demo", FLAGS[2])
    card("ocr", "Dzongkha OCR Dataset", "Computer vision · in development",
         "Crowdsourced handwritten Dzongkha dataset with a full pipeline (intake, labelling, dedup, QA) and a trained OCR model.",
         ["Python", "CV", "Data pipeline"], "in development", FLAGS[0])
    card("parking", "GMC Smart Parking", "Pelsung Cohort 2",
         "Real-time parking discovery, reservation and navigation with camera-based detection, for Gelephu Mindfulness City.",
         ["Computer Vision", "Full-stack"], "pelsung cohort 2", FLAGS[3])
    timeline()
    stack()
    button("portfolio", "Portfolio", "◎", GOLD)
    button("linkedin", "LinkedIn", "in", FLAGS[0])
    button("email", "Email", "@", FLAGS[3])
    button("resume", "Resume", "≡", FLAGS[2])
    footer()
