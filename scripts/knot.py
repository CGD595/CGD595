"""Geometry for the traditional endless knot (dpal be'u).

Classic construction: an n x n woven lattice (n odd) of straight ribbons.
On every side neighbouring ribbons are joined by square U-turns, and the one
ribbon left over on each side turns the corner to meet its neighbour. Every
turn encloses a small square hole, which gives the knot its "rings".
n=3 is the 9-crossing textbook form; n=5 (used here) has 25 crossings.
For odd n this is always a single closed strand.
"""
import math

N = 5


def _ends_pairing(n):
    pr = [(("T", k), ("T", k + 1)) for k in range(1, n, 2)]
    pr.append((("T", n), ("R", 1)))
    pr += [(("R", k), ("R", k + 1)) for k in range(2, n + 1, 2)]
    pr += [(("B", k), ("B", k - 1)) for k in range(n, 1, -2)]
    pr.append((("B", 1), ("L", n)))
    pr += [(("L", k), ("L", k + 1)) for k in range(1, n, 2)]
    return pr


def _corners(n=N):
    """Centerline as a closed rectilinear polygon (grid units), plus crossing visits."""
    p = [2 * i for i in range(n)]
    P = p[-1]

    def stub(e):
        s, k = e
        i = k - 1
        return {"T": (p[i], -2), "B": (p[i], P + 2), "L": (-2, p[i]), "R": (P + 2, p[i])}[s]

    through = {}
    for k in range(1, n + 1):
        through[("L", k)], through[("R", k)] = ("R", k), ("L", k)
        through[("T", k)], through[("B", k)] = ("B", k), ("T", k)
    arc = {}
    for a, b in _ends_pairing(n):
        arc[a], arc[b] = b, a

    pts = []
    start = e = ("L", 1)
    while True:
        f = through[e]
        pts.append(stub(e))
        pts.append(stub(f))
        g = arc[f]
        if f[0] != g[0]:  # corner turn: go round the outer corner point
            a, b = stub(f), stub(g)
            pts.append((b[0], a[1]) if f[0] in "TB" else (a[0], b[1]))
        e = g
        if e == start:
            break
    # drop consecutive duplicates
    out = []
    for q in pts:
        if not out or out[-1] != q:
            out.append(q)
    return out, p


def knot(size, cx, cy, step=0.05):
    """Dense closed polyline fitted to size (rotated 45 deg), cumulative lengths,
    indices of over-crossings, and the grid unit in px."""
    corners, p = _corners()
    lattice = set(p)
    dense, over = [], []
    for a, b in zip(corners, corners[1:] + corners[:1]):
        horiz = a[1] == b[1]
        L = abs(b[0] - a[0]) + abs(b[1] - a[1])
        n = max(1, round(L / step))
        for s in range(n):
            t = s / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if s and abs(x - round(x)) < 1e-9 and abs(y - round(y)) < 1e-9:
                xi, yi = round(x), round(y)
                if xi in lattice and yi in lattice:
                    i, j = p.index(xi), p.index(yi)
                    if horiz == ((i + j) % 2 == 0):
                        over.append(len(dense))
            dense.append((x, y))
    c = p[-1] / 2
    rot = [((x - c) - (y - c), (x - c) + (y - c)) for x, y in dense]
    rot = [(u / math.sqrt(2), v / math.sqrt(2)) for u, v in rot]
    span = (p[-1] + 4) * math.sqrt(2) + 1  # outer extent incl. ribbon width
    unit = size / span
    P = [(cx + u * unit, cy + v * unit) for u, v in rot]
    cum = [0.0]
    for i in range(1, len(P) + 1):
        cum.append(cum[-1] + math.dist(P[i - 1], P[i % len(P)]))
    return P, cum, over, unit


def slice_path(P, cum, s0, s1):
    """Points of the closed polyline between arc lengths s0..s1 (wraps)."""
    total = cum[-1]

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
        t = (s - cum[lo]) / ((cum[lo + 1] - cum[lo]) or 1)
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), lo

    p0, i0 = at(s0)
    p1, i1 = at(s1)
    out, n, i = [p0], len(P), i0 + 1
    steps = 0
    while (i % n) != ((i1 + 1) % n) and steps < n:
        out.append(P[i % n])
        i += 1
        steps += 1
    out.append(p1)
    return out
