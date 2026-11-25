# "16-bit RPG" skin: pixel art like a 90s console role-playing game. Twice
# the detail of the 8-bit skin, four-tone shading lit from the top left,
# colored outlines instead of black ones, and dithered fog.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_rpg.py -- art/rpg.blend
#
# Each picture is a 48 x 48 grid rendered at 10 pixels per cell and
# installed with hard edges.

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

N = 48
CELL = 2.25 / N

# Color ramps: outline, deep shadow, shadow, mid, light, highlight.
RAMP = {
    "sun": ("#8A3B12", "#D9661F", "#F29A2E", "#FFC23D", "#FFE07A", "#FFF6C9"),
    "ray": ("#8A3B12", "#C2501C", "#D9661F", "#F29A2E", "#FFB84D", "#FFD27A"),
    "moon": ("#4B4A7A", "#9C9CC8", "#C4C4E0", "#E4E2F2", "#F4F2FA", "#FFFFFF"),
    "star": ("#7A5A12", "#E0A21C", "#F2C230", "#FFE066", "#FFF0A8", "#FFFFFF"),
    "cloud": ("#4A5590", "#8A93C4", "#AEB7DD", "#D8DEF5", "#F2F4FF", "#FFFFFF"),
    "dark": ("#262B4A", "#454D7A", "#5A6390", "#727CA8", "#8C95BF", "#A9B1D6"),
    "rain": ("#1B3F8A", "#2E63C2", "#3F86E0", "#5EA8F2", "#9ACDFF", "#D9EEFF"),
    "snow": ("#4A6A9A", "#9DB8DA", "#C2D6EE", "#E2ECF8", "#F4F8FF", "#FFFFFF"),
    "bolt": ("#8A5A12", "#E0A21C", "#F2C230", "#FFE14D", "#FFF08A", "#FFFFFF"),
    "fog": ("#5A6390", "#8A93C4", "#AEB7DD", "#C9CFEA", "#E2E6F6", "#F2F4FF"),
}


def circle(cx, cy, r):
    return {(x, y) for x in range(N) for y in range(N) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def rect(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def run(cells, x, y, dx, dy, cap=4):
    n = 0
    while n < cap and (x + dx * (n + 1), y + dy * (n + 1)) in cells:
        n += 1
    return n


def shade(cells, ramp):
    """Tone each cell by how far it is from the lit (top-left) and the dark
    (bottom-right) edge, and outline the shape in the ramp's darkest color."""
    out_c, deep, shadow, mid, light, hi = RAMP[ramp]
    s = {}
    for x, y in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in cells and 0 <= p[0] < N and 0 <= p[1] < N:
                s[p] = out_c
    for x, y in cells:
        a = min(run(cells, x, y, -1, 1), run(cells, x, y, 0, 1))  # toward the light
        b = min(run(cells, x, y, 1, -1), run(cells, x, y, 0, -1))  # away from it
        if a == 0:
            t = hi
        elif b == 0:
            t = deep
        elif b == 1:
            t = shadow
        elif a == 1:
            t = light
        else:
            t = mid
        s[(x, y)] = t
    return s


def place(name, cells, z):
    c = kit.coll(name)
    by = {}
    for p, col in cells.items():
        if 0 <= p[0] < N and 0 <= p[1] < N:
            by.setdefault(col, []).append(p)
    for col, ps in by.items():
        me = bpy.data.meshes.new(f"{name}_{col}")
        bm = bmesh.new()
        for x, y in ps:
            x0, y0 = (x - N / 2) * CELL, (y - N / 2) * CELL
            vs = [bm.verts.new(v) for v in ((x0, y0, 0), (x0 + CELL, y0, 0), (x0 + CELL, y0 + CELL, 0), (x0, y0 + CELL, 0))]
            bm.faces.new(vs)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=CELL * 0.01)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(kit.flat(col))
        o = bpy.data.objects.new(f"{name}_{col}", me)
        o.location.z = z
        c.objects.link(o)


def sun(cx, cy, r):
    s = {}
    import math
    for i in range(8):
        a = 2 * math.pi * i / 8
        ray = set()
        for k in range(4):
            d = r + 3 + k
            w = 1.6 - k * 0.3
            ray |= circle(cx + d * math.cos(a), cy + d * math.sin(a), w)
        s.update(shade(ray, "ray"))
    s.update(shade(circle(cx, cy, r), "sun"))
    return s


def moon(cx, cy, r):
    body = circle(cx, cy, r) - circle(cx + r * 0.55, cy + r * 0.4, r * 0.85)
    s = shade(body, "moon")
    for x, y, cr in ((-0.5, -0.1, 1.6), (-0.2, -0.6, 1.2), (-0.62, 0.35, 0.9)):
        for p in circle(cx + x * r, cy + y * r, cr):
            if p in body and s[p] not in (RAMP["moon"][0], RAMP["moon"][5]):
                s[p] = RAMP["moon"][2]
    return s


def star(cx, cy, k):
    cells = {(cx, cy)}
    for d in range(1, k + 1):
        cells |= {(cx + d, cy), (cx - d, cy), (cx, cy + d), (cx, cy - d)}
    cells |= {(cx + 1, cy + 1), (cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1)} if k > 2 else set()
    return shade(cells, "star")


def cloud(cx, cy, k, dark=False):
    cells = (circle(cx - 6 * k, cy + 3.2 * k, 3.6 * k) | circle(cx, cy + 5 * k, 5.2 * k)
             | circle(cx + 6 * k, cy + 3.4 * k, 3.4 * k)
             | rect(round(cx - 8.5 * k), round(cy), round(cx + 8.5 * k) - 1, round(cy + 3 * k)))
    cells = {(x, y) for x, y in cells if y >= round(cy)}
    return shade(cells, "dark" if dark else "cloud")


def drops(points, length):
    s = {}
    for x, y in points:
        cells = {(x - i // 3 + w, y - i) for i in range(length) for w in (0, 1)}
        s.update(shade(cells, "rain"))
    return s


def flakes(points):
    s = {}
    for x, y in points:
        cells = {(x + d, y) for d in range(-3, 4)} | {(x, y + d) for d in range(-3, 4)}
        cells |= {(x + d, y + d) for d in (-2, -1, 1, 2)} | {(x + d, y - d) for d in (-2, -1, 1, 2)}
        s.update(shade(cells, "snow"))
    return s


def bolt(x0, y0):
    rows = [(7, 13), (7, 12), (6, 12), (6, 11), (5, 11), (5, 10), (4, 10), (4, 9), (3, 15), (2, 15), (2, 14),
            (7, 13), (7, 12), (6, 12), (6, 11), (6, 10), (5, 10), (5, 9), (5, 8), (4, 7), (4, 6), (3, 5)]
    cells = set()
    for i, (a, b) in enumerate(rows):
        cells |= {(x0 + x, y0 - i) for x in range(a, b + 1)}
    return shade(cells, "bolt")


def fog():
    s = {}
    ramp = RAMP["fog"]
    for i, (x0, y0, x1) in enumerate(((8, 36, 36), (12, 28, 42), (6, 20, 36), (13, 12, 41))):
        band = rect(x0, y0, x1, y0 + 3)
        s.update(shade(band, "fog"))
        # Dithered fade at both ends, the classic 16-bit trick.
        for x in list(range(x0, x0 + 4)) + list(range(x1 - 3, x1 + 1)):
            for y in range(y0, y0 + 4):
                if (x + y) % 2:
                    s.pop((x, y), None)
        for x in range(x0 - 1, x1 + 2):
            for y in (y0 - 1, y0 + 4):
                if (x <= x0 + 3 or x >= x1 - 3) and s.get((x, y)) == ramp[0]:
                    s.pop((x, y))
    return s


scene = kit.setup(samples=4, res=N * 10, gpu=False)
scene.cycles.filter_width = 0.01  # no smoothing between cells

place("sun", sun(24, 24, 10), 0)
place("sun_small", sun(17, 31, 7), 0)
place("moon", moon(24, 24, 15), 0)
place("moon_small", moon(17, 31, 10), 0)
st = {}
for x, y, k in ((39, 39, 3), (42, 24, 2), (32, 44, 2), (8, 9, 3), (9, 40, 2)):
    st.update(star(x, y, k))
place("stars", st, 0)
place("cloud_small", cloud(28, 12, 1.25), 0.1)
place("cloud_big", cloud(24, 14, 1.85), 0.1)
place("cloud_top", cloud(24, 23, 1.75), 0.1)
place("cloud_dark_top", cloud(24, 23, 1.75, dark=True), 0.1)
place("rain", drops(((12, 18), (21, 15), (30, 18), (39, 14), (16, 8), (26, 6), (35, 7)), 6), 0)
place("drizzle", drops(((12, 17), (21, 13), (30, 17), (39, 12), (16, 7), (28, 6), (35, 8)), 2), 0)
place("snow", flakes(((12, 15), (24, 11), (36, 15), (17, 4), (31, 4))), 0)
sl = drops(((12, 18), (30, 17), (22, 8)), 6)
sl.update(flakes(((22, 15), (37, 11), (12, 5), (33, 4))))
place("sleet", sl, 0)
place("bolt", bolt(16, 22), 0)
place("fog", fog(), 0)
kit.save()
