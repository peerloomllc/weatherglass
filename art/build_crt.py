# "CRT Terminal" skin: green phosphor line art on a black screen, with a
# soft glow around every line and dark scanlines across it.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_crt.py -- art/crt.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

G = "#33FF66"  # phosphor green
SCAN = 0.5  # how dark the gaps between scanlines are
W = 0.042  # line width

LINE = kit.flat(G, scan=SCAN)
GLOW = kit.flat(G, 0.14, scan=SCAN)
SCREEN = kit.flat("#050A06")  # black fill, so a cloud hides what is behind it
DIM = kit.flat("#0F4A20", scan=SCAN)  # dim green fill for dark clouds


def line(c, pts, z, closed=True, w=W):
    kit.stroke(c, GLOW, pts, w * 3.4, z, closed, "glow")
    kit.stroke(c, LINE, pts, w, z, closed, "line")


def seg(x, y, length, angle):
    dx, dy = length / 2 * math.cos(angle), length / 2 * math.sin(angle)
    return [(x - dx, y - dy), (x + dx, y + dy)]


class Crt(kit.Style):
    def sun(self, c, x, y, s, z):
        line(c, kit.circle_pts(x, y, 0.3 * s), z)
        for i in range(8):
            a = 2 * math.pi * i / 8
            line(c, [(x + 0.42 * s * math.cos(a), y + 0.42 * s * math.sin(a)),
                     (x + 0.6 * s * math.cos(a), y + 0.6 * s * math.sin(a))], z, closed=False)

    def moon(self, c, x, y, s, z):
        line(c, kit.crescent_pts(x, y, 0.5 * s), z)

    def star(self, c, x, y, r, z):
        for a in (0, math.pi / 2):
            line(c, seg(x, y, r * 1.6, a), z, closed=False, w=W * 0.8)

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, DIM if dark else SCREEN, pts, z, "fill")
        line(c, pts, z)

    def raindrop(self, c, x, y, z):
        line(c, seg(x, y, 0.22, math.radians(72)), z, closed=False)

    def drizzle(self, c, x, y, z):
        line(c, seg(x, y, 0.07, math.radians(72)), z, closed=False)

    def flake(self, c, x, y, r, z):
        for i in range(3):
            line(c, seg(x, y, r * 1.8, math.pi / 2 + i * math.pi / 3), z, closed=False, w=W * 0.85)

    def fog(self, c, bars, z):
        # Dashed lines, like a row of hyphens on the terminal.
        for x, y, w in bars:
            n = int(w / 0.22)
            x0 = x - w / 2
            for i in range(n):
                line(c, [(x0 + i * 0.22, y), (x0 + i * 0.22 + 0.15, y)], z, closed=False)

    def bolt(self, c, x, y, s, z):
        pts = kit.bolt_pts(x, y, s, 1.15)
        kit.poly(c, SCREEN, pts, z, "fill")
        line(c, pts, z)


kit.build(Crt())
kit.save()
