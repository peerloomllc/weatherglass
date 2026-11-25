# "Watercolor" skin: soft washes of paint on white paper. Each wash is
# blotchy, pools darker at its edge as it dries, and darkens where it
# overlaps another.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_watercolor.py -- art/watercolor.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials


def body(color, alpha=0.55):
    return kit.flat(color, alpha, alpha_grain=0.22, grain_scale=5)


def rim(color, alpha=0.5):
    return kit.flat(color, alpha, alpha_grain=0.25, grain_scale=14)


def wash(c, pts, color, z, alpha=0.55, edge=0.028):
    """A wash: blotchy paint plus a darker edge where the pigment dried."""
    kit.poly(c, body(color, alpha), pts, z, "wash")
    kit.stroke(c, rim(color, min(1.0, alpha + 0.15)), pts, edge, z, True, "edge")


class Watercolor(kit.Style):
    def sun(self, c, x, y, s, z):
        wash(c, kit.circle_pts(x, y, 0.62 * s), "#F9D56E", z, 0.45, 0.02)
        wash(c, kit.circle_pts(x + 0.02 * s, y - 0.02 * s, 0.44 * s), "#F2A541", z, 0.6)

    def moon(self, c, x, y, s, z):
        wash(c, kit.crescent_pts(x, y, 0.55 * s), "#8FA9D6", z, 0.6)

    def star(self, c, x, y, r, z):
        kit.poly(c, body("#E8B84A", 0.85), kit.star_pts(x, y, r * 1.3, 5, 0.45), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        if dark:
            wash(c, kit.cloud_outline(x, y, s), "#5B6E8C", z, 0.6)
            wash(c, kit.cloud_outline(x - 0.04 * s, y + 0.06 * s, s, 0.72), "#3E4F6B", z, 0.35, 0.015)
        else:
            wash(c, kit.cloud_outline(x, y, s), "#A7C4E0", z, 0.42)
            wash(c, kit.cloud_outline(x + 0.03 * s, y - 0.06 * s, s, 0.7), "#7FA3C9", z, 0.25, 0.015)

    def raindrop(self, c, x, y, z):
        wash(c, kit.drop_pts(x, y, 0.085, 0.25), "#3C7FC1", z, 0.65, 0.018)

    def drizzle(self, c, x, y, z):
        wash(c, kit.circle_pts(x, y, 0.045, 32), "#3C7FC1", z, 0.6, 0.014)

    def flake(self, c, x, y, r, z):
        for arm in kit.flake_arms(x, y, r * 1.15, 0.055):
            kit.poly(c, body("#6FA8DC", 0.7), arm, z, "flake")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, kit.flat("#9AAABB" if i % 2 else "#B9C4CF", 0.5, alpha_grain=0.25, grain_scale=8, stretch=6),
                     kit.capsule_pts(x, y, w, 0.2, 0.0, taper=0.5), z, "fog")

    def bolt(self, c, x, y, s, z):
        wash(c, kit.bolt_pts(x, y, s, 1.18), "#F2C94C", z, 0.85, 0.022)


kit.build(Watercolor())
kit.save()
