# "Ukiyo-e" skin: a Japanese woodblock print. Indigo outlines, flat inks
# with a faint wood grain, a vermilion sun that darkens toward its edge,
# clouds crossed by bands of mist, and rain as fine straight lines.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_ukiyoe.py -- art/ukiyoe.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

INDIGO = "#1F2A44"
OW = 0.024


def ink(color, alpha=1.0):
    # Flat ink with a faint wood grain running sideways.
    return kit.flat(color, alpha, grain=0.16, grain_scale=14, stretch=7)


class Ukiyoe(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.disc(c, ink(INDIGO), x, y, 0.56 * s + OW, z, "line")
        kit.disc(c, kit.radial("#E8673E", "#A8392A"), x, y, 0.56 * s, z, "sun", unit=True)

    def moon(self, c, x, y, s, z):
        kit.disc(c, ink(INDIGO), x, y, 0.54 * s + OW, z, "line")
        kit.disc(c, kit.radial("#FBF4E2", "#E9CF8E"), x, y, 0.54 * s, z, "moon", unit=True)

    def star(self, c, x, y, r, z):
        kit.disc(c, ink(INDIGO), x, y, r * 0.4, z, "star")

    def cloud(self, c, x, y, s, z, dark):
        fill, band = ("#7D8799", "#4A5670") if dark else ("#F7EFDC", "#9DBBCB")
        kit.cloud_flat(c, ink(INDIGO), x, y, s, z, grow=1.06)
        kit.cloud_flat(c, ink(fill), x, y, s, z)
        # Bands of mist across the lower half, the classic print device.
        for dx, dy, w in ((-0.1, -0.04, 0.85), (0.04, -0.2, 0.95)):
            kit.poly(c, ink(band), kit.capsule_pts(x + dx * s, y + dy * s, w * s, 0.07 * s), z, "mist")

    def raindrop(self, c, x, y, z):
        for dx, dy, ln in ((0, 0, 0.5), (0.09, 0.12, 0.36), (-0.07, 0.1, 0.3)):
            kit.poly(c, ink(INDIGO), kit.capsule_pts(x + dx, y + dy, ln, 0.018, math.radians(82)), z, "line")

    def drizzle(self, c, x, y, z):
        kit.poly(c, ink(INDIGO), kit.capsule_pts(x, y, 0.16, 0.018, math.radians(82)), z, "line")

    def flake(self, c, x, y, r, z):
        kit.disc(c, ink(INDIGO), x, y, r * 0.5 + OW * 0.8, z, "line")
        kit.disc(c, ink("#FBF6EA"), x, y, r * 0.5, z, "snow")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, ink("#8DB3C7" if i % 2 else "#B9CED6", 0.9), kit.capsule_pts(x, y, w, 0.15), z, "mist")
            kit.poly(c, ink(INDIGO), kit.capsule_pts(x, y - 0.075, w * 0.85, 0.012), z, "edge")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, ink(INDIGO), kit.bolt_pts(x, y, s, 1.28), z, "line")
        kit.poly(c, ink("#D9A441"), kit.bolt_pts(x, y, s, 1.12), z, "bolt")


kit.setup()
kit.build(Ukiyoe())
kit.save()
