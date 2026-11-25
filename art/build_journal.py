# "Field journal" skin: a naturalist's sketchbook. Loose brown ink lines
# drawn by hand, over pale watercolor tints that do not quite line up with
# the ink.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_journal.py -- art/journal.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

INK = kit.flat("#4A3526", 0.92, alpha_grain=0.08, grain_scale=60)
W = 0.022
TINT = (0.035, -0.03)  # how far the tint sits from the ink


def tint(color, alpha=0.5):
    return kit.flat(color, alpha, alpha_grain=0.18, grain_scale=6)


def ink(c, pts, z, closed=True, w=W, seed=0.0):
    kit.stroke(c, INK, kit.wobble(pts, 0.006, seed), w, z, closed, "ink")


def tinted(c, pts, color, z, alpha=0.5):
    kit.poly(c, tint(color, alpha), [(x + TINT[0], y + TINT[1]) for x, y in pts], z, "tint")


class Journal(kit.Style):
    def sun(self, c, x, y, s, z):
        tinted(c, kit.circle_pts(x, y, 0.42 * s), "#F2C14E", z, 0.6)
        ink(c, kit.circle_pts(x, y, 0.36 * s, 48), z)
        for i in range(12):
            a = 2 * math.pi * i / 12
            r0, r1 = 0.46 * s, (0.7 if i % 2 == 0 else 0.6) * s
            ink(c, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], z, False, seed=i)

    def moon(self, c, x, y, s, z):
        pts = kit.crescent_pts(x, y, 0.55 * s, steps=40)
        tinted(c, pts, "#B9C6DE", z, 0.6)
        ink(c, pts, z)

    def star(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * 0.7 * math.cos(a), r * 0.7 * math.sin(a)
            ink(c, [(x - dx, y - dy), (x + dx, y + dy)], z, False, W * 0.8, i)

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, kit.flat("#F3EAD7"), pts, z, "paper")  # hides anything behind
        tinted(c, pts, "#6F7F96" if dark else "#B7C9DA", z, 0.6 if dark else 0.45)
        ink(c, pts[::3], z)
        if dark:
            # Quick shading strokes along the bottom.
            for i in range(7):
                px = x + (-0.42 + i * 0.14) * s
                ink(c, [(px, y - 0.3 * s), (px + 0.08 * s, y - 0.18 * s)], z, False, W * 0.7, i)

    def raindrop(self, c, x, y, z):
        tinted(c, kit.circle_pts(x - 0.02, y - 0.06, 0.04, 24), "#5E8FC4", z, 0.6)
        ink(c, [(x + 0.03, y + 0.1), (x - 0.03, y - 0.08)], z, False, seed=x * 7)

    def drizzle(self, c, x, y, z):
        tinted(c, kit.circle_pts(x, y, 0.035, 24), "#5E8FC4", z, 0.6)
        ink(c, kit.circle_pts(x, y, 0.025, 16), z, True, W * 0.8)

    def flake(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * math.cos(a), r * math.sin(a)
            ink(c, [(x - dx, y - dy), (x + dx, y + dy)], z, False, W * 0.9, i + x * 5)

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            tinted(c, kit.capsule_pts(x, y, w, 0.12), "#A9B4BF", z, 0.45)
            ink(c, [(x - w / 2 + w * k / 20, y + 0.015 * math.sin(k * 1.3 + i)) for k in range(21)], z, False, seed=i)

    def bolt(self, c, x, y, s, z):
        pts = kit.bolt_pts(x, y, s, 1.15)
        tinted(c, pts, "#F2C14E", z, 0.75)
        ink(c, pts, z)


kit.build(Journal())
kit.save()
