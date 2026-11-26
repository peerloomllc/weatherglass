# "Whitepaper" skin (Bitcoin group): thin black ink on off-white paper,
# drawn like the diagrams in the 2008 Bitcoin paper. Plain outlined shapes
# with the Bitcoin sign in the sun and the clouds, and rain drawn as
# diagram arrows.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_whitepaper.py -- art/whitepaper.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

INK = "#141414"
W = 0.05  # line width
PAPER = "#FBFAF6"  # fill so shapes in front hide lines behind them
SHADE = "#D9D6CC"  # the grey fill of rain clouds


def ink(alpha=1.0):
    return kit.flat(INK, alpha)


def arrow(c, x0, y0, x1, y1, z, w=W, head=0.09):
    """A straight line from (x0, y0) to (x1, y1) with a filled arrowhead."""
    a = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - head * math.cos(a), y1 - head * math.sin(a)
    kit.stroke(c, ink(), [(x0, y0), (bx, by)], w, z, False, "arrow")
    side = head * 0.6
    kit.poly(c, ink(), [(x1, y1), (bx + side * math.sin(a), by - side * math.cos(a)),
                        (bx - side * math.sin(a), by + side * math.cos(a))], z, "head")


class Whitepaper(kit.Style):
    def sun(self, c, x, y, s, z):
        r = 0.34 * s
        kit.disc(c, kit.flat(PAPER), x, y, r, z, "fill")
        kit.stroke(c, ink(), kit.circle_pts(x, y, r), W, z, True, "sun")
        kit.btc(c, ink(), x, y, 0.42 * s, 0.06, z)
        for i in range(8):
            a = 2 * math.pi * i / 8 + math.pi / 8
            kit.stroke(c, ink(), [(x + 0.47 * s * math.cos(a), y + 0.47 * s * math.sin(a)),
                                  (x + 0.66 * s * math.cos(a), y + 0.66 * s * math.sin(a))], W, z, False, "ray")

    def moon(self, c, x, y, s, z):
        pts = kit.crescent_pts(x, y, 0.55 * s)
        kit.poly(c, kit.flat(PAPER), pts, z, "fill")
        kit.stroke(c, ink(), pts, W, z, True, "moon")

    def star(self, c, x, y, r, z):
        kit.disc(c, ink(), x, y, r * 0.42, z, "node")

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, kit.flat(SHADE if dark else PAPER), pts, z, "fill")
        kit.stroke(c, ink(), pts, W, z, True, "cloud")
        kit.btc(c, ink(), x + 0.02 * s, y + 0.04 * s, 0.34 * s, 0.055, z)
        if dark:
            # Hatching along the bottom, like a shaded diagram box.
            for i in range(-4, 5):
                hx = x + i * 0.12 * s
                kit.stroke(c, ink(0.85), [(hx - 0.05 * s, y - 0.3 * s), (hx + 0.05 * s, y - 0.18 * s)], W * 0.6, z,
                           False, "hatch")

    def raindrop(self, c, x, y, z):
        arrow(c, x + 0.05, y + 0.2, x - 0.03, y - 0.1, z)

    def drizzle(self, c, x, y, z):
        arrow(c, x + 0.02, y + 0.09, x - 0.01, y - 0.06, z, W * 0.8, 0.07)

    def flake(self, c, x, y, r, z):
        for i in range(3):
            a = math.pi / 2 + i * math.pi / 3
            kit.stroke(c, ink(), [(x - r * 1.1 * math.cos(a), y - r * 1.1 * math.sin(a)),
                                  (x + r * 1.1 * math.cos(a), y + r * 1.1 * math.sin(a))], W * 0.8, z, False, "flake")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            pts = [(x - w / 2, y), (x + w / 2, y)]
            if i % 2:
                kit.dashed(c, ink(), pts, W, 0.16, 0.08, z, False, "fog")
            else:
                kit.stroke(c, ink(), pts, W, z, False, "fog")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, ink(), kit.bolt_pts(x, y, s, 1.2), z, "bolt")


kit.setup()
kit.build(Whitepaper())
kit.save()
