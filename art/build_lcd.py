# "LCD watch" skin: the black segments of a calculator or digital watch on
# grey-green glass. Every shape casts a faint shadow on the mirror behind
# the glass, a little down and to the right.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_lcd.py -- art/lcd.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

SEG = kit.flat("#1F2A1A")
SHADOW = kit.flat("#1F2A1A", 0.2)
GLASS = kit.flat("#9AA882")  # the screen color, so a cloud hides what is behind it
OFF = (0.028, -0.028)  # shadow offset


def bar(x, y, length, width, angle):
    """A straight-ended segment, centred on (x, y)."""
    ca, sa = math.cos(angle), math.sin(angle)
    hl, hw = length / 2, width / 2
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]


def seg(c, pts, z, m=None):
    kit.poly(c, SHADOW, [(x + OFF[0], y + OFF[1]) for x, y in pts], z, "shadow")
    kit.poly(c, m or SEG, pts, z, "seg")


def line(c, pts, w, z):
    kit.stroke(c, SHADOW, [(x + OFF[0], y + OFF[1]) for x, y in pts], w, z, True, "shadow")
    kit.stroke(c, SEG, pts, w, z, True, "seg")


class Lcd(kit.Style):
    def sun(self, c, x, y, s, z):
        seg(c, kit.circle_pts(x, y, 0.27 * s, 48), z)
        for i in range(8):
            a = 2 * math.pi * i / 8
            seg(c, bar(x + 0.5 * s * math.cos(a), y + 0.5 * s * math.sin(a), 0.16 * s, 0.07 * s, a), z)

    def moon(self, c, x, y, s, z):
        seg(c, kit.crescent_pts(x, y, 0.5 * s), z)

    def star(self, c, x, y, r, z):
        seg(c, kit.star_pts(x, y, r * 1.2, 4, 0.3), z)

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        if dark:
            seg(c, pts, z)
        else:
            # An outline only, filled with the glass color.
            kit.poly(c, SHADOW, [(px + OFF[0], py + OFF[1]) for px, py in pts], z, "shadow")
            kit.poly(c, GLASS, pts, z, "glass")
            kit.stroke(c, SEG, pts, 0.07, z, True, "seg")

    def raindrop(self, c, x, y, z):
        seg(c, bar(x, y, 0.2, 0.055, math.radians(70)), z)

    def drizzle(self, c, x, y, z):
        seg(c, bar(x, y, 0.07, 0.07, 0.0), z)

    def flake(self, c, x, y, r, z):
        for i in range(3):
            seg(c, bar(x, y, r * 1.9, 0.05, math.pi / 2 + i * math.pi / 3), z)

    def fog(self, c, bars, z):
        for x, y, w in bars:
            n = int(w / 0.2)
            x0 = x - w / 2 + 0.07
            for i in range(n):
                seg(c, bar(x0 + i * 0.2, y, 0.15, 0.07, 0.0), z)

    def bolt(self, c, x, y, s, z):
        seg(c, kit.bolt_pts(x, y, s, 1.15), z)


kit.build(Lcd())
kit.save()
