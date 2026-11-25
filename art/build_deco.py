# "Art Deco" skin: gold on black, like a 1920s cinema or hotel lobby.
# Sunbursts of long thin rays, double gold outlines and diamond tips.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_deco.py -- art/deco.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

GOLD = kit.flat("#D4AF37")
PALE = kit.flat("#F3E5AB")
NIGHT = kit.flat("#16130E")  # the background color, so a cloud hides what is behind it
SMOKE = kit.flat("#4A3C1C")  # dark cloud fill


def diamond(x, y, r, tall=1.6):
    return [(x, y + r * tall), (x + r, y), (x, y - r * tall), (x - r, y)]


class Deco(kit.Style):
    def sun(self, c, x, y, s, z):
        for i in range(24):
            a = 2 * math.pi * i / 24
            long = 0.86 if i % 2 == 0 else 0.68
            w = 0.045
            pts = [(x + 0.36 * s * math.cos(a - w), y + 0.36 * s * math.sin(a - w)),
                   (x + long * s * math.cos(a), y + long * s * math.sin(a)),
                   (x + 0.36 * s * math.cos(a + w), y + 0.36 * s * math.sin(a + w))]
            kit.poly(c, GOLD if i % 2 == 0 else PALE, pts, z, "ray")
        kit.disc(c, GOLD, x, y, 0.4 * s, z, "sun")
        kit.stroke(c, NIGHT, kit.circle_pts(x, y, 0.32 * s), 0.025 * s, z, True, "ring")
        kit.disc(c, PALE, x, y, 0.2 * s, z, "core")

    def moon(self, c, x, y, s, z):
        kit.stroke(c, GOLD, kit.circle_pts(x, y, 0.62 * s), 0.02 * s, z, True, "ring")
        kit.poly(c, GOLD, kit.crescent_pts(x, y, 0.52 * s), z, "moon")
        kit.poly(c, PALE, kit.crescent_pts(x - 0.03 * s, y - 0.03 * s, 0.4 * s, 0.9, 0.5, 0.36), z, "shine")

    def star(self, c, x, y, r, z):
        kit.poly(c, PALE, kit.star_pts(x, y, r * 1.5, 4, 0.18), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, SMOKE if dark else NIGHT, pts, z, "fill")
        kit.stroke(c, GOLD, pts, 0.035, z, True, "line")
        kit.stroke(c, PALE if not dark else GOLD, kit.cloud_outline(x, y + 0.03 * s, s, 0.82), 0.014, z, True, "inner")

    def raindrop(self, c, x, y, z):
        kit.stroke(c, GOLD, [(x, y + 0.12), (x, y - 0.08)], 0.018, z, False, "line")
        kit.poly(c, PALE, diamond(x, y - 0.12, 0.035), z, "tip")

    def drizzle(self, c, x, y, z):
        kit.poly(c, GOLD, diamond(x, y, 0.035), z, "tip")

    def flake(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * 1.1 * math.cos(a), r * 1.1 * math.sin(a)
            kit.stroke(c, GOLD, [(x - dx, y - dy), (x + dx, y + dy)], 0.018, z, False, "arm")
            for sgn in (1, -1):
                kit.poly(c, PALE, diamond(x + sgn * dx, y + sgn * dy, 0.025, 1.0), z, "tip")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            for k, off in enumerate((-0.04, 0.0, 0.04)):
                kit.stroke(c, GOLD if k != 1 else PALE, [(x - w / 2 + abs(off) * 2, y + off), (x + w / 2 - abs(off) * 2, y + off)],
                           0.016, z, False, "line")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, GOLD, kit.bolt_pts(x, y, s, 1.25), z, "bolt")
        kit.poly(c, NIGHT, kit.bolt_pts(x, y, s, 0.95), z, "inset")
        kit.poly(c, PALE, kit.bolt_pts(x, y, s, 0.7), z, "core")


kit.build(Deco())
kit.save()
