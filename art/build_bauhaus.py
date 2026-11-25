# "Bauhaus" skin: weather built from plain circles, half circles, bars and
# triangles in red, yellow, blue and black, like a 1920s Bauhaus poster.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_bauhaus.py -- art/bauhaus.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

RED, YELLOW, BLUE, BLACK, GREY = (kit.flat(h) for h in ("#D62828", "#F7B801", "#1D4E89", "#111111", "#A9B8C4"))


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def bar(x, y, length, width, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    hl, hw = length / 2, width / 2
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]


class Bauhaus(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.poly(c, RED, kit.sector_pts(x - 0.1 * s, y - 0.1 * s, 0.6 * s, math.pi, 2 * math.pi), z, "half")
        kit.disc(c, YELLOW, x, y, 0.46 * s, z, "sun")
        kit.poly(c, BLACK, bar(x, y + 0.62 * s, 0.07 * s, 0.22 * s, 0), z, "ray")
        kit.poly(c, BLACK, bar(x + 0.62 * s, y, 0.22 * s, 0.07 * s, 0), z, "ray")

    def moon(self, c, x, y, s, z):
        kit.poly(c, BLUE, kit.crescent_pts(x, y, 0.52 * s), z, "moon")
        kit.disc(c, YELLOW, x + 0.32 * s, y - 0.3 * s, 0.1 * s, z, "dot")

    def star(self, c, x, y, r, z):
        kit.poly(c, BLACK, bar(x, y, r * 0.9, r * 0.9, math.pi / 4), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        m = BLUE if dark else GREY
        # A bar with three half circles standing on it.
        kit.poly(c, m, rect(x - 0.6 * s, y - 0.32 * s, x + 0.6 * s, y - 0.04 * s), z, "base")
        for cx, r in ((-0.33, 0.27), (0.08, 0.38), (0.42, 0.18)):
            kit.poly(c, m, kit.sector_pts(x + cx * s, y - 0.04 * s, r * s, 0, math.pi), z, "half")

    def raindrop(self, c, x, y, z):
        kit.poly(c, BLACK, bar(x, y, 0.05, 0.22, 0), z, "rain")

    def drizzle(self, c, x, y, z):
        kit.disc(c, BLACK, x, y, 0.045, z, "drop")

    def flake(self, c, x, y, r, z):
        kit.poly(c, BLUE, kit.ring_pts(x, y, r * 0.55, r * 0.3), z, "snow")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, BLACK if i % 2 else GREY, rect(x - w / 2, y - 0.07, x + w / 2, y + 0.07), z, "fog")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, RED, kit.bolt_pts(x, y, s, 1.2), z, "bolt")


kit.build(Bauhaus())
kit.save()
