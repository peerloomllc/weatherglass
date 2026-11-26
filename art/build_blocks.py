# "Block explorer" skin (Bitcoin group): every weather symbol built from
# small square blocks on one grid, like a blockchain explorer drawing blocks
# as they are mined. Each block is its own object named "cell", so the
# opening clip (animate_clip.py, style "mine") can drop them in one by one.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_blocks.py -- art/blocks.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

STEP = 0.15  # grid spacing
GAP = 0.03  # space between blocks


def inside(pts, x, y):
    """Is (x, y) inside the polygon (even-odd rule)?"""
    n, hit = len(pts), False
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def block(c, colors, x, y, size=STEP - GAP, z=0.0):
    """One square block, lit from the top: light on top, darker below."""
    h = size / 2
    r = size * 0.18
    pts = []
    for cx, cy, a0 in ((x + h - r, y + h - r, 0), (x - h + r, y + h - r, 90), (x - h + r, y - h + r, 180),
                       (x + h - r, y - h + r, 270)):
        for i in range(4):
            a = math.radians(a0 + 30 * i)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return kit.poly(c, kit.gradient(colors, h), pts, z, "cell")


def fill(c, colors, pts, z, step=STEP):
    """Blocks on every grid point inside the shape."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    i0, i1 = math.floor(min(xs) / step), math.ceil(max(xs) / step)
    j0, j1 = math.floor(min(ys) / step), math.ceil(max(ys) / step)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            if inside(pts, i * step, j * step):
                block(c, colors, i * step, j * step, step - GAP * step / STEP, z)


def snap(v):
    return round(v / STEP) * STEP


ORANGE = ("#C76A06", "#F7931A", "#FFB54D")
GOLD = ("#C9962A", "#FFD27A", "#FFE9B3")
LIGHT = ("#8FA0B8", "#C7D3E3", "#EEF3F9")
DARK = ("#3E4B5E", "#5C6B80", "#7C8BA0")
BLUE = ("#1F6FB8", "#3BA3F5", "#8CCBFF")
WHITE = ("#BFD0E0", "#FFFFFF", "#FFFFFF")
FOG = ("#56657C", "#7F92AD", "#A3B3C9")
BOLT = ("#D9A400", "#FFD23F", "#FFF0A8")


class Blocks(kit.Style):
    def sun(self, c, x, y, s, z):
        fill(c, ORANGE, kit.circle_pts(x, y, 0.44 * s), z)
        # Rays: a block out from the sun in eight directions.
        for i in range(8):
            a = 2 * math.pi * i / 8
            for d in (0.66,):
                block(c, ORANGE, snap(x + d * s * math.cos(a)), snap(y + d * s * math.sin(a)), z=z)

    def moon(self, c, x, y, s, z):
        fill(c, GOLD, kit.crescent_pts(x, y, 0.55 * s), z)

    def star(self, c, x, y, r, z):
        sx, sy = snap(x), snap(y)
        block(c, GOLD, sx, sy, z=z)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            block(c, GOLD, sx + dx * STEP * 0.62, sy + dy * STEP * 0.62, STEP * 0.4, z)

    def cloud(self, c, x, y, s, z, dark):
        fill(c, DARK if dark else LIGHT, kit.cloud_outline(x, y, s), z)

    def raindrop(self, c, x, y, z):
        # A short chain of three blocks.
        sx, sy = snap(x), snap(y)
        for k in range(3):
            block(c, BLUE, sx, sy + k * STEP, STEP * (0.62 + 0.12 * k), z)

    def drizzle(self, c, x, y, z):
        block(c, BLUE, snap(x), snap(y), STEP * 0.62, z)

    def flake(self, c, x, y, r, z):
        block(c, WHITE, x, y, STEP * 0.6, z)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            block(c, WHITE, x + dx * STEP * 0.5, y + dy * STEP * 0.5, STEP * 0.32, z)

    def fog(self, c, bars, z):
        for x, y, w in bars:
            sy = snap(y)
            for i in range(round((x - w / 2) / STEP), round((x + w / 2) / STEP) + 1):
                block(c, FOG, i * STEP, sy, z=z)

    def bolt(self, c, x, y, s, z):
        # A zigzag of whole blocks, top to bottom.
        sx, sy = snap(x), snap(y)
        for i, j in ((0, 2), (1, 2), (-1, 1), (0, 1), (-1, 0), (0, 0), (1, 0), (0, -1), (-1, -2)):
            block(c, BOLT, sx + i * STEP, sy + j * STEP, z=z)


kit.setup()
kit.build(Blocks())
kit.save()
