# "Chalkboard" skin: weather drawn in chalk on a green school board. Lines
# wobble like a hand drawing, the chalk is broken and dusty, and dark
# clouds are smudged in.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_chalk.py -- art/chalk.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

WHITE, YELLOW, BLUE = "#F4F4EC", "#F7E37A", "#9BD3F2"
W = 0.034


def chalk(color, alpha=0.95):
    # Chalk catches on the board, so the line breaks up into dust.
    return kit.flat(color, alpha, alpha_grain=0.45, grain_scale=95, stretch=1.5)


def smudge(color, alpha):
    return kit.flat(color, alpha, alpha_grain=0.15, grain_scale=10, stretch=3)


def wobble(pts, amp=0.008, seed=0.0):
    """Nudge each point a little, smoothly, so lines look hand drawn."""
    out = []
    for i, (x, y) in enumerate(pts):
        t = i * 0.35 + seed
        out.append((x + amp * math.sin(t * 1.7) + amp * 0.5 * math.sin(t * 4.1),
                    y + amp * math.cos(t * 1.3) + amp * 0.5 * math.sin(t * 3.3)))
    return out


def line(c, pts, color, z, closed=True, w=W, seed=0.0):
    kit.stroke(c, chalk(color), wobble(pts, seed=seed), w, z, closed, "chalk")


def hatch(c, x, y, r, color, z, step=0.06, angle=math.radians(35)):
    """Diagonal shading lines filling a circle."""
    ca, sa = math.cos(angle), math.sin(angle)
    k = -r + step / 2
    i = 0
    while k < r:
        half = math.sqrt(max(r * r - k * k, 0)) * 0.92
        p0 = (x + k * -sa - half * ca, y + k * ca - half * sa)
        p1 = (x + k * -sa + half * ca, y + k * ca + half * sa)
        kit.stroke(c, chalk(color, 0.6), wobble([p0, p1], 0.004, i), W * 0.5, z, False, "hatch")
        k += step
        i += 1


class Chalk(kit.Style):
    def sun(self, c, x, y, s, z):
        hatch(c, x, y, 0.38 * s, YELLOW, z)
        line(c, kit.circle_pts(x, y, 0.4 * s, 60), YELLOW, z)
        for i in range(9):
            a = 2 * math.pi * i / 9 + 0.2
            line(c, [(x + 0.52 * s * math.cos(a), y + 0.52 * s * math.sin(a)),
                     (x + 0.72 * s * math.cos(a), y + 0.72 * s * math.sin(a))], YELLOW, z, False, seed=i)

    def moon(self, c, x, y, s, z):
        line(c, kit.crescent_pts(x, y, 0.55 * s, steps=40), WHITE, z)

    def star(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * 0.8 * math.cos(a), r * 0.8 * math.sin(a)
            line(c, [(x - dx, y - dy), (x + dx, y + dy)], YELLOW, z, False, W * 0.7, i)

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, kit.flat("#2E4A3A"), pts, z, "board")  # hides anything behind
        kit.poly(c, smudge(WHITE, 0.4 if dark else 0.12), pts, z, "smudge")
        line(c, pts[::3], WHITE, z)

    def raindrop(self, c, x, y, z):
        line(c, [(x + 0.04, y + 0.1), (x - 0.03, y - 0.1)], BLUE, z, False, seed=x * 9)

    def drizzle(self, c, x, y, z):
        line(c, [(x + 0.015, y + 0.03), (x - 0.01, y - 0.03)], BLUE, z, False, seed=x * 9)

    def flake(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * math.cos(a), r * math.sin(a)
            line(c, [(x - dx, y - dy), (x + dx, y + dy)], WHITE, z, False, W * 0.8, i + x * 5)

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            pts = [(x - w / 2 + w * k / 30, y + 0.025 * math.sin(k * 0.9 + i)) for k in range(31)]
            line(c, pts, WHITE, z, False, seed=i * 3)

    def bolt(self, c, x, y, s, z):
        pts = kit.bolt_pts(x, y, s, 1.15)
        kit.poly(c, smudge(YELLOW, 0.3), pts, z, "smudge")
        line(c, pts, YELLOW, z)


kit.build(Chalk())
kit.save()
