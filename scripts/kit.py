"""Shared design kit: tokens, fonts and an SVG document builder.

Tokens mirror chimegd.xyz (near-black base, one emerald accent,
Space Grotesk for display, Roboto for body). Fonts are subset per SVG
and embedded, so GitHub renders the real typefaces inside <img>.
"""
import base64
import io
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path(__file__).resolve().parent / "fonts"

THEMES = {
    "dark": dict(
        bg="#0D0D0D", card="#141414", border="#242424", fg="#F5F5F5", muted="#858585", faint="#4A4A4A",
        primary="#13AE6B", on_primary="#0A0A0A", blind="#0A2319", blind_op=0.5, aurora="#0B653E", aurora_op=0.55,
        sweep_op=0.07, off="#262626",
    ),
    "light": dict(
        bg="#FAFAFA", card="#F3F3F3", border="#E0E0E0", fg="#0F0F0F", muted="#707070", faint="#B5B5B5",
        primary="#014226", on_primary="#FFFFFF", blind="#014226", blind_op=0.05, aurora="#2FB57A", aurora_op=0.16,
        sweep_op=0.06, off="#DADADA",
    ),
}

# family alias -> file
FONTS = {
    "h": "SpaceGrotesk-Bold.ttf",    # display
    "m": "SpaceGrotesk-Medium.ttf",  # labels, arrows
    "b": "Roboto-Regular.ttf",       # body
}
EASE = "cubic-bezier(.22,1,.36,1)"


@lru_cache(None)
def _font(alias):
    return TTFont(FONT_DIR / FONTS[alias])


@lru_cache(None)
def _metrics(alias):
    f = _font(alias)
    return f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm


def measure(text, font="b", size=16, track=0.0):
    """Advance width in px (kerning is disabled in CSS so this is exact)."""
    cmap, hmtx, upm = _metrics(font)
    w = 0
    for ch in text:
        g = cmap.get(ord(ch))
        w += hmtx[g][0] if g else upm * 0.5
    return w * size / upm + track * size * len(text)


def wrap(text, width, font="b", size=16, track=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if measure(trial, font, size, track) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def _subset_b64(alias, chars):
    f = TTFont(FONT_DIR / FONTS[alias])
    opts = Options()
    opts.flavor = "woff"
    opts.hinting = False
    opts.layout_features = []
    opts.name_IDs = []
    opts.notdef_outline = True
    s = Subsetter(opts)
    s.populate(text="".join(sorted(chars)) + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


BASE_CSS = """
text{font-kerning:none;text-rendering:geometricPrecision}
.h{font-family:CGDh,'Space Grotesk',system-ui,sans-serif}
.m{font-family:CGDm,'Space Grotesk',system-ui,sans-serif}
.b{font-family:CGDb,Roboto,system-ui,sans-serif}
.sweep{animation:sweep 9s %s infinite both}
@keyframes sweep{0%%{transform:translateX(-260px)}55%%,100%%{transform:translateX(1500px)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}.sweep{display:none}}
""" % EASE


class Doc:
    def __init__(self, w, h, theme, label):
        self.w, self.h, self.t, self.label = w, h, THEMES[theme], label
        self.used = {k: set() for k in FONTS}
        self.parts, self.css, self.defs = [], "", []

    def add(self, s):
        self.parts.append(s)
        return self

    def text(self, x, y, txt, font="b", size=16, fill=None, track=0.0, anchor="start", cls="", style="", raw=False):
        self.used[font].update(txt)
        fill = fill or self.t["fg"]
        ls = f' letter-spacing="{track}em"' if track else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        st = f' style="{style}"' if style else ""
        body = txt if raw else escape(txt)
        klass = f"{font} {cls}".strip()
        return f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" font-size="{size}" fill="{fill}"{ls}{an}{st}>{body}</text>'

    def tspan_text(self, x, y, spans, font="b", size=16, track=0.0, cls="", style=""):
        """spans: [(text, fill, font_override_or_None)]"""
        out = []
        for s, fill, f in spans:
            self.used[f or font].update(s)
            fc = f' class="{f}"' if f else ""
            out.append(f'<tspan fill="{fill}"{fc}>{escape(s)}</tspan>')
        ls = f' letter-spacing="{track}em"' if track else ""
        st = f' style="{style}"' if style else ""
        return f'<text x="{x:.1f}" y="{y:.1f}" class="{font} {cls}" font-size="{size}" xml:space="preserve"{ls}{st}>{"".join(out)}</text>'

    def render(self):
        faces = "".join(
            f"@font-face{{font-family:CGD{k};src:url(data:font/woff;base64,{_subset_b64(k, v)}) format('woff')}}"
            for k, v in self.used.items() if v
        )
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-label="{escape(self.label)}">'
            f"<style>{faces}{BASE_CSS}{self.css}</style>{defs}\n" + "\n".join(self.parts) + "\n</svg>\n"
        )

    def save(self, name, theme):
        out = ROOT / "assets" / theme / name
        out.parent.mkdir(parents=True, exist_ok=True)
        data = self.render()
        out.write_text(data, encoding="utf-8")
        return len(data)


def sparkle(cx, cy, r, fill, extra=""):
    """Four-point star (the ✦ used across the site)."""
    k = r * 0.28
    d = (f"M{cx} {cy-r} Q{cx+k} {cy-k} {cx+r} {cy} Q{cx+k} {cy+k} {cx} {cy+r} "
         f"Q{cx-k} {cy+k} {cx-r} {cy} Q{cx-k} {cy-k} {cx} {cy-r}Z")
    return f'<path d="{d}" fill="{fill}" {extra}/>'
