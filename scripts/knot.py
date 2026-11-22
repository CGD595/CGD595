"""Geometry for a single-strand endless knot.

A 4x4 woven lattice whose 16 line ends are joined by non-crossing outer
loops. The pairing below was found by exhaustive search: it is the
rotationally symmetric layout that closes into exactly one strand.
"""
import math

N = 4
PAIRS = [
    (("T", 1), ("T", 2)), (("T", 3), ("L", 1)), (("T", 4), ("R", 3)), (("R", 1), ("R", 2)),
    (("R", 4), ("B", 2)), (("B", 4), ("B", 3)), (("B", 1), ("L", 2)), (("L", 4), ("L", 3)),
]


def _path(g=1.0, h_turn=0.8, h_petal=2.3, res=60):
    L = (N + 1) * g

    def end(e):
        s, k = e
        return {"L": ((0, k * g), (-1, 0)), "R": ((L, k * g), (1, 0)),
                "T": ((k * g, 0), (0, -1)), "B": ((k * g, L), (0, 1))}[s]

    through = {}
    for k in range(1, N + 1):
        through[("L", k)], through[("R", k)] = ("R", k), ("L", k)
        through[("T", k)], through[("B", k)] = ("B", k), ("T", k)
    arc = {}
    for a, b in PAIRS:
        arc[a], arc[b] = b, a

    pts, crossings = [], []
    start = e = ("L", 1)
    while True:
        f = through[e]
        (x0, y0), _ = end(e)
        (x1, y1), _ = end(f)
        for i in range(res):
            t = i / res
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            # lattice crossing?  (every res/(N+1) steps)
            if i and i % (res // (N + 1)) == 0:
                horiz = e[0] in "LR"
                ci, cj = (round(x / g), round(y / g))
                crossings.append((len(pts), ci, cj, horiz))
            pts.append((x, y))
        g2 = arc[f]
        (ax, ay), (adx, ady) = end(f)
        (bx, by), (bdx, bdy) = end(g2)
        h = (h_turn if f[0] == g2[0] else h_petal) * g
        c1, c2 = (ax + adx * h, ay + ady * h), (bx + bdx * h, by + bdy * h)
        m = res if f[0] == g2[0] else int(res * 2.4)
        for i in range(m):
            t = i / m
            u = 1 - t
            pts.append((u**3 * ax + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * bx,
                        u**3 * ay + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * by))
        e = g2
        if e == start:
            break
    return pts, crossings, L


def knot(size, cx, cy):
    """Returns (points, cumulative lengths, total, over_indices) fitted into a size x size box."""
    pts, crossings, L = _path()
    rot = [((x - L / 2 - (y - L / 2)) / math.sqrt(2), (x - L / 2 + (y - L / 2)) / math.sqrt(2)) for x, y in pts]
    xs, ys = [p[0] for p in rot], [p[1] for p in rot]
    s = size / max(max(xs) - min(xs), max(ys) - min(ys))
    mx, my = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    P = [(cx + (x - mx) * s, cy + (y - my) * s) for x, y in rot]
    cum = [0.0]
    for i in range(1, len(P) + 1):
        a, b = P[i - 1], P[i % len(P)]
        cum.append(cum[-1] + math.dist(a, b))
    # alternating weave: horizontal strand is over when i+j is even
    over = [idx for idx, i, j, horiz in crossings if horiz == ((i + j) % 2 == 0)]
    return P, cum, over


def slice_path(P, cum, s0, s1):
    """Points of the closed polyline between arc lengths s0..s1 (s may wrap)."""
    total = cum[-1]
    out = []

    def at(s):
        s %= total
        lo, hi = 0, len(cum) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        a, b = P[lo % len(P)], P[(lo + 1) % len(P)]
        seg = cum[lo + 1] - cum[lo] or 1
        t = (s - cum[lo]) / seg
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), lo

    p0, i0 = at(s0)
    p1, i1 = at(s1)
    out.append(p0)
    i = i0 + 1
    n = len(P)
    steps = 0
    while (i % n) != ((i1 + 1) % n) and steps < n:
        out.append(P[i % n])
        i += 1
        steps += 1
    out.append(p1)
    return out
