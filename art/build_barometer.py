# "Ship's barometer" skin: polished brass and cream enamel, like the dial
# of an old ship's instrument. A compass-rose sun, brass outlines and
# engraved lines.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_barometer.py -- art/barometer.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

BRASS = ["#7A5A26", "#E8C77E", "#B08A45"]  # dark to bright to mid, bottom to top
ENAMEL = kit.flat("#EFE6D2")
NAVY = kit.flat("#1A2E4A")
ENGRAVE = kit.flat("#5C4419")


def brass(extent):
    return kit.gradient(BRASS, extent)


def rim(c, pts, z, w=0.04):
    kit.stroke(c, kit.flat("#B08A45"), pts, w, z, True, "rim")


class Barometer(kit.Style):
    def sun(self, c, x, y, s, z):
        # Compass rose: four long points and four short ones.
        for i in range(8):
            a = math.pi / 2 + i * math.pi / 4
            long = 0.82 if i % 2 == 0 else 0.55
            w = 0.13 * s
            tip = (x + long * s * math.cos(a), y + long * s * math.sin(a))
            l = (x + w * math.cos(a + math.pi / 2), y + w * math.sin(a + math.pi / 2))
            r = (x + w * math.cos(a - math.pi / 2), y + w * math.sin(a - math.pi / 2))
            kit.poly(c, brass(long * s), [l, tip, (x, y)], z, "point")
            kit.poly(c, kit.flat("#8C6A2F"), [(x, y), tip, r], z, "point")
        kit.disc(c, ENAMEL, x, y, 0.2 * s, z, "face")
        kit.stroke(c, kit.flat("#B08A45"), kit.circle_pts(x, y, 0.2 * s), 0.025 * s, z, True, "rim")
        kit.disc(c, ENGRAVE, x, y, 0.04 * s, z, "pin")

    def moon(self, c, x, y, s, z):
        pts = kit.crescent_pts(x, y, 0.55 * s)
        kit.poly(c, brass(0.55 * s), pts, z, "moon")
        kit.stroke(c, ENGRAVE, kit.crescent_pts(x - 0.04 * s, y - 0.03 * s, 0.42 * s, 0.9, 0.55, 0.4), 0.012, z, True, "engrave")

    def star(self, c, x, y, r, z):
        kit.poly(c, kit.flat("#E8C77E"), kit.star_pts(x, y, r * 1.4, 4, 0.28), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        pts = kit.cloud_outline(x, y, s)
        kit.poly(c, kit.flat("#5E6B7D") if dark else ENAMEL, pts, z, "enamel")
        rim(c, pts, z)
        kit.stroke(c, ENGRAVE if not dark else kit.flat("#B08A45"), kit.cloud_outline(x, y + 0.02 * s, s, 0.84), 0.01, z, True,
                   "engrave")

    def raindrop(self, c, x, y, z):
        kit.poly(c, brass(0.15), kit.drop_pts(x, y, 0.085, 0.25), z, "drop")

    def drizzle(self, c, x, y, z):
        kit.disc(c, kit.flat("#E8C77E"), x, y, 0.045, z, "drop")

    def flake(self, c, x, y, r, z):
        for arm in kit.flake_arms(x, y, r * 1.15, 0.05):
            kit.poly(c, kit.flat("#E8C77E"), arm, z, "flake")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            pts = kit.capsule_pts(x, y, w, 0.14)
            kit.poly(c, ENAMEL if i % 2 else kit.flat("#C9BFA8"), pts, z, "fog")
            rim(c, pts, z, 0.025)

    def bolt(self, c, x, y, s, z):
        kit.poly(c, brass(0.45 * s), kit.bolt_pts(x, y, s, 1.2), z, "bolt")
        kit.stroke(c, ENGRAVE, kit.bolt_pts(x, y, s, 0.8), 0.01, z, True, "engrave")


kit.build(Barometer())
kit.save()
