# "Blueprint" skin: white technical line drawings on blueprint blue, with
# dashed construction lines, centre marks and dimension ticks.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_blueprint.py -- art/blueprint.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

LINE = kit.flat("#FFFFFF")
FAINT = kit.flat("#FFFFFF", 0.55)
PAPER = kit.flat("#0C4C88")  # the blueprint color, so a cloud hides what is behind it
SHADE = kit.flat("#FFFFFF", 0.22)  # dark cloud fill
W = 0.03  # main line width
F = 0.012  # construction line width


def centre(c, x, y, r, z):
    """A centre mark: two thin crossing lines."""
    kit.stroke(c, FAINT, [(x - r, y), (x + r, y)], F, z, False, "mark")
    kit.stroke(c, FAINT, [(x, y - r), (x, y + r)], F, z, False, "mark")


class Blueprint(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.dashed(c, FAINT, kit.circle_pts(x, y, 0.72 * s, 120), F, 0.04, 0.03, z)
        centre(c, x, y, 0.5 * s, z)
        kit.stroke(c, LINE, kit.circle_pts(x, y, 0.32 * s), W, z, True, "sun")
        for i in range(8):
            a = 2 * math.pi * i / 8 + math.pi / 8
            kit.stroke(c, LINE, [(x + 0.44 * s * math.cos(a), y + 0.44 * s * math.sin(a)),
                                 (x + 0.62 * s * math.cos(a), y + 0.62 * s * math.sin(a))], W, z, False, "ray")

    def moon(self, c, x, y, s, z):
        r = 0.55 * s
        # The circle the crescent is cut with, drawn as a construction line.
        kit.dashed(c, FAINT, kit.circle_pts(x + 0.5 * r, y + 0.36 * r, 0.82 * r, 120), F, 0.04, 0.03, z)
        centre(c, x, y, 0.25 * s, z)
        kit.stroke(c, LINE, kit.crescent_pts(x, y, r), W, z, True, "moon")

    def star(self, c, x, y, r, z):
        centre(c, x, y, r * 0.9, z)
        kit.stroke(c, LINE, kit.circle_pts(x, y, r * 0.35, 24), F * 1.4, z, True, "star")

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, PAPER, pts, z, "fill")
        if dark:
            kit.poly(c, SHADE, pts, z, "shade")
        circles, _ = kit.cloud_shapes(x, y, s)
        for cx, cy, r in circles:
            kit.dashed(c, FAINT, kit.circle_pts(cx, cy, r, 72), F, 0.03, 0.03, z)
        kit.stroke(c, LINE, pts, W, z, True, "cloud")
        # A dimension line under the cloud with end ticks.
        y0 = y - 0.46 * s
        x0, x1 = x - 0.66 * s, x + 0.66 * s
        kit.stroke(c, FAINT, [(x0, y0), (x1, y0)], F, z, False, "dim")
        for xx in (x0, x1):
            kit.stroke(c, FAINT, [(xx, y0 - 0.04), (xx, y0 + 0.04)], F, z, False, "tick")

    def raindrop(self, c, x, y, z):
        kit.stroke(c, LINE, [(x + 0.04, y + 0.1), (x - 0.04, y - 0.1)], W * 0.8, z, False, "rain")

    def drizzle(self, c, x, y, z):
        kit.stroke(c, LINE, kit.circle_pts(x, y, 0.035, 24), W * 0.7, z, True, "drop")

    def flake(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            dx, dy = r * math.cos(a), r * math.sin(a)
            kit.stroke(c, LINE, [(x - dx, y - dy), (x + dx, y + dy)], W * 0.7, z, False, "arm")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            if i % 2:
                kit.dashed(c, LINE, [(x - w / 2, y), (x + w / 2, y)], W, 0.12, 0.06, z, False)
            else:
                kit.stroke(c, LINE, [(x - w / 2, y), (x + w / 2, y)], W, z, False, "fog")

    def bolt(self, c, x, y, s, z):
        pts = kit.bolt_pts(x, y, s, 1.15)
        kit.poly(c, PAPER, pts, z, "fill")
        kit.stroke(c, LINE, pts, W, z, True, "bolt")


kit.build(Blueprint())
kit.save()
