# "Teletext" skin: the chunky block graphics of a TV text service, in its
# eight pure colors on black. Each picture is a 24 x 24 grid of blocks,
# rendered at 15 pixels per block and installed with hard edges, like the
# 8-bit skin.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_teletext.py -- art/teletext.blend

import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

N = 24
CELL = 2.25 / N

C = {"white": "#FFFFFF", "yellow": "#FFFF00", "cyan": "#00FFFF", "green": "#00FF00",
     "magenta": "#FF00FF", "red": "#FF0000", "blue": "#0000FF"}


def circle(cx, cy, r):
    return {(x, y) for x in range(N) for y in range(N) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def rect(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def place(name, cells, z):
    """cells: {(x, y): color name}. One mesh of squares per color."""
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
        me.materials.append(kit.flat(C[col]))
        o = bpy.data.objects.new(f"{name}_{col}", me)
        o.location.z = z
        c.objects.link(o)


def paint(cells, col, into=None):
    d = into if into is not None else {}
    d.update({p: col for p in cells})
    return d


def sun(cx, cy, r):
    s = {}
    for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        d = round(r + 2) if dx == 0 or dy == 0 else round((r + 2) * 0.75)
        paint(rect(cx + dx * d - 1, cy + dy * d - 1, cx + dx * d, cy + dy * d), "red", s)
    return paint(circle(cx, cy, r), "yellow", s)


def moon(cx, cy, r):
    return paint(circle(cx, cy, r) - circle(cx + r * 0.55, cy + r * 0.4, r * 0.85), "white")


def cloud(cx, cy, k, dark):
    body = (circle(cx - 4 * k, cy + 2.3 * k, 2.6 * k) | circle(cx, cy + 3.6 * k, 3.8 * k)
            | circle(cx + 4.2 * k, cy + 2.4 * k, 2.5 * k) | rect(round(cx - 6 * k), round(cy), round(cx + 6 * k) - 1, round(cy + 2 * k)))
    body = {(x, y) for x, y in body if y >= round(cy)}
    s = paint(body, "white")
    if dark:
        low = min(y for _, y in body)
        paint({(x, y) for x, y in body if y <= low + 1}, "blue", s)
        paint({(x, y) for x, y in body if y == low + 2}, "cyan", s)
    return s


def drops(points, length, col="cyan"):
    s = {}
    for x, y in points:
        paint({(x, y - i) for i in range(length)}, col, s)
    return s


def flakes(points):
    s = {}
    for x, y in points:
        paint({(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}, "white", s)
    return s


def bolt(x0, y0):
    rows = [(3, 5), (2, 4), (2, 4), (1, 3), (1, 6), (3, 5), (3, 4), (2, 3), (2, 2)]
    s = {}
    for i, (a, b) in enumerate(rows):
        paint({(x0 + x, y0 - i) for x in range(a, b + 1)}, "yellow", s)
    return s


def fog():
    s = {}
    for i, (x0, y, x1) in enumerate(((4, 17, 18), (6, 13, 21), (3, 9, 17), (7, 5, 20))):
        col = "cyan" if i % 2 else "green"
        paint({(x, y) for x in range(x0, x1 + 1) if (x - x0) % 4 != 3}, col, s)
    return s


scene = kit.setup(samples=4, res=N * 15, gpu=False)
scene.cycles.filter_width = 0.01  # no smoothing between blocks

place("sun", sun(12, 12, 5), 0)
place("sun_small", sun(8, 15, 3.5), 0)
place("moon", moon(12, 12, 7), 0)
place("moon_small", moon(8, 15, 5), 0)
place("stars", paint({(19, 19), (21, 12), (16, 22), (4, 4), (5, 20)}, "white"), 0)
place("cloud_small", cloud(15, 4, 1.0, False), 0.1)
place("cloud_big", cloud(12, 6, 1.5, False), 0.1)
place("cloud_top", cloud(12, 11, 1.4, False), 0.1)
place("cloud_dark_top", cloud(12, 11, 1.4, True), 0.1)
place("rain", drops(((5, 9), (9, 8), (13, 9), (17, 8), (7, 4), (11, 3), (15, 4), (19, 4)), 3), 0)
place("drizzle", drops(((6, 8), (10, 6), (14, 8), (18, 6), (8, 3), (16, 3)), 1), 0)
place("snow", flakes(((6, 8), (12, 6), (18, 8), (9, 3), (15, 3))), 0)
sl = drops(((6, 9), (14, 9), (19, 5)), 3)
sl.update(flakes(((10, 6), (17, 8), (7, 3), (14, 3))))
place("sleet", sl, 0)
place("bolt", bolt(9, 10), 0)
place("fog", fog(), 0)
kit.save()
