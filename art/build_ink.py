# "Ink wash" skin: sumi-e brush painting on rice paper. Grey ink washes
# that darken where they overlap, tapered brush strokes, a brush-circle
# moon and a red seal for the sun.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_ink.py -- art/ink.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

INK = "#1A1A1A"


def wash(alpha, streak=1.0):
    # Ink that soaks into the paper unevenly.
    return kit.flat(INK, alpha, alpha_grain=alpha * 0.35, grain_scale=9, stretch=streak)


def brush(alpha=0.88):
    # A loaded brush dragged sideways: solid with dry streaks.
    return kit.flat(INK, alpha, alpha_grain=0.22, grain_scale=16, stretch=6)


class Ink(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.disc(c, kit.flat("#B22222", 0.92, alpha_grain=0.18, grain_scale=20), x, y, 0.5 * s, z, "seal")

    def moon(self, c, x, y, s, z):
        kit.disc(c, wash(0.12), x, y, 0.5 * s, z, "wash")
        kit.poly(c, brush(), kit.ring_pts(x, y, 0.6 * s, 0.52 * s, math.radians(110), math.radians(110 + 330), taper=0.85),
                 z, "enso")

    def star(self, c, x, y, r, z):
        kit.disc(c, wash(0.8), x, y, r * 0.32, z, "dot")

    def cloud(self, c, x, y, s, z, dark):
        # A light wash for the shape, then soft-edged blooms on top: dense
        # in the middle, fading at the rim, darker where they overlap.
        kit.cloud_flat(c, wash(0.4 if dark else 0.16), x, y, s, z)
        a = 0.6 if dark else 0.32
        circles, _ = kit.cloud_shapes(x, y, s)
        circles += [(x + dx * s, y - 0.2 * s, 0.24 * s) for dx in (-0.45, 0.0, 0.42)]
        for cx, cy, r in circles:
            kit.disc(c, kit.radial(INK, INK, a, 0.0), cx, cy, r * 0.95, z, "wash", unit=True)
        # One firm stroke along the bottom.
        kit.poly(c, brush(), kit.capsule_pts(x - 0.02 * s, y - 0.34 * s, 1.2 * s, 0.07 * s, 0.0, taper=0.8), z, "stroke")

    def raindrop(self, c, x, y, z):
        for dx, dy, ln in ((0, 0, 0.4), (0.12, 0.16, 0.28)):
            kit.poly(c, brush(0.85), kit.capsule_pts(x + dx, y + dy, ln, 0.034, math.radians(-104), taper=0.85), z, "stroke")

    def drizzle(self, c, x, y, z):
        kit.poly(c, brush(0.8), kit.capsule_pts(x, y, 0.13, 0.03, math.radians(-104), taper=0.7), z, "stroke")

    def flake(self, c, x, y, r, z):
        kit.poly(c, brush(0.8), kit.ring_pts(x, y, r * 0.55, r * 0.32), z, "ring")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, wash(0.28, streak=6), kit.capsule_pts(x, y, w, 0.16, 0.0, taper=0.7), z, "fog")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, brush(0.92), kit.bolt_pts(x, y, s, 1.15), z, "bolt")


kit.setup()
kit.build(Ink())
kit.save()
