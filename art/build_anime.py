# "Anime" skin: cel-shaded like a bright anime sky. Flat colors with a
# shadow tone, blue outlines, a glowing sun and sparkles.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_anime.py -- art/anime.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

INK = "#24508F"  # outline color
OW = 0.028  # outline width


def f(color, alpha=1.0):
    return kit.flat(color, alpha)


def outlined_disc(c, x, y, r, fill, z):
    kit.disc(c, f(INK), x, y, r + OW, z, "line")
    kit.disc(c, f(fill), x, y, r, z, "fill")


def outlined_poly(c, pts, fill, z, k):
    kit.poly(c, f(INK), kit.grow_pts(pts, k), z, "line")
    kit.poly(c, f(fill), pts, z, "fill")


class Anime(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.disc(c, kit.radial("#FFFBE0", "#FFE680", 0.9, 0.0), x, y, 0.95 * s, z, "glow", unit=True)
        for i in range(12):
            a = 2 * math.pi * i / 12 + math.pi / 12
            long = 0.86 if i % 2 == 0 else 0.72
            w = 0.07
            pts = [(x + 0.5 * s * math.cos(a - w), y + 0.5 * s * math.sin(a - w)),
                   (x + long * s * math.cos(a), y + long * s * math.sin(a)),
                   (x + 0.5 * s * math.cos(a + w), y + 0.5 * s * math.sin(a + w))]
            kit.poly(c, f("#FFD23F"), pts, z, "ray")
        kit.disc(c, f("#FFB830"), x, y, 0.52 * s, z, "sun_edge")
        kit.disc(c, f("#FFE14D"), x, y, 0.47 * s, z, "sun")
        kit.disc(c, f("#FFF6C2"), x - 0.12 * s, y + 0.12 * s, 0.17 * s, z, "shine")
        kit.poly(c, f("#FFFFFF"), kit.star_pts(x + 0.55 * s, y + 0.5 * s, 0.13 * s, 4, 0.25), z, "glint")

    def moon(self, c, x, y, s, z):
        pts = kit.crescent_pts(x, y, 0.55 * s)
        outlined_poly(c, pts, "#FFF3B0", z, 1.07)
        kit.poly(c, f("#F5CF5F"), kit.crescent_pts(x - 0.04 * s, y - 0.04 * s, 0.47 * s, 0.95, 0.42, 0.3), z, "shade")

    def star(self, c, x, y, r, z):
        kit.poly(c, f("#FFF8D0"), kit.star_pts(x, y, r * 1.3, 4, 0.25), z, "sparkle")

    def cloud(self, c, x, y, s, z, dark):
        shadow, body = ("#6B7FA8", "#9FB2D6") if dark else ("#BFD6F2", "#FFFFFF")
        kit.cloud_flat(c, f(INK), x, y, s, z, grow=1.08)
        kit.cloud_flat(c, f(shadow), x, y, s, z)
        kit.cloud_flat(c, f(body), x, y, s, z, grow=0.92, dy=0.035)

    def raindrop(self, c, x, y, z):
        kit.poly(c, f(INK), kit.drop_pts(x, y, 0.1 + OW * 0.8, 0.3), z, "line")
        kit.poly(c, f("#5EB8FF"), kit.drop_pts(x, y, 0.1, 0.3), z, "drop")
        kit.disc(c, f("#E6F5FF"), x - 0.035, y - 0.02, 0.028, z, "shine")

    def drizzle(self, c, x, y, z):
        outlined_disc(c, x, y, 0.05, "#5EB8FF", z)

    def flake(self, c, x, y, r, z):
        for arm in kit.flake_arms(x, y, r * 1.2 + OW, 0.05 + 2 * OW):
            kit.poly(c, f(INK), arm, z, "line")
        for arm in kit.flake_arms(x, y, r * 1.2, 0.05):
            kit.poly(c, f("#FFFFFF"), arm, z, "flake")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, f(INK), kit.capsule_pts(x, y, w + 2 * OW, 0.17 + 2 * OW), z, "line")
            kit.poly(c, f("#BFD6F2"), kit.capsule_pts(x, y, w, 0.17), z, "shadow")
            kit.poly(c, f("#FFFFFF"), kit.capsule_pts(x - 0.01, y + 0.025, w - 0.04, 0.11), z, "fog")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, f(INK), kit.bolt_pts(x, y, s, 1.3), z, "line")
        kit.poly(c, f("#FFE14D"), kit.bolt_pts(x, y, s, 1.15), z, "bolt")
        kit.poly(c, f("#FFF6C2"), kit.bolt_pts(x, y, s, 0.6), z, "shine")


kit.setup()
kit.build(Anime())
kit.save()
