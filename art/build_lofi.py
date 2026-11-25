# "Lo-fi" skin: the view from a cosy bedroom window at dusk. Soft purple,
# peach and lilac gradients with gentle glows, like a lo-fi music video.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_lofi.py -- art/lofi.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials


def glow(c, x, y, r, color, z, alpha=0.45):
    kit.disc(c, kit.radial(color, color, alpha, 0.0), x, y, r, z, "glow", unit=True)


class Lofi(kit.Style):
    def sun(self, c, x, y, s, z):
        glow(c, x, y, 0.9 * s, "#FFB27A", z, 0.5)
        r = 0.45 * s
        kit.poly(c, kit.gradient(["#FF7E6B", "#FFC38A"], r), kit.circle_pts(x, y, r), z, "sun")

    def moon(self, c, x, y, s, z):
        glow(c, x, y, 0.8 * s, "#E2D6FF", z, 0.25)
        r = 0.52 * s
        kit.poly(c, kit.gradient(["#C9B6FF", "#F6EEFF"], r), kit.crescent_pts(x, y, r), z, "moon")

    def star(self, c, x, y, r, z):
        glow(c, x, y, r * 1.6, "#FFE9C9", z, 0.5)
        kit.disc(c, kit.flat("#FFF4E0"), x, y, r * 0.3, z, "star")

    def cloud(self, c, x, y, s, z, dark):
        cols = ["#4E4470", "#8E7AB5"] if dark else ["#A98FC9", "#F2D6E8"]
        kit.poly(c, kit.gradient(cols, 0.32 * s), kit.cloud_outline(x, y, s), z, "cloud")

    def raindrop(self, c, x, y, z):
        kit.poly(c, kit.flat("#8EC5FF", 0.9), kit.capsule_pts(x, y, 0.2, 0.045, math.radians(76)), z, "rain")

    def drizzle(self, c, x, y, z):
        kit.disc(c, kit.flat("#8EC5FF", 0.9), x, y, 0.04, z, "drop")

    def flake(self, c, x, y, r, z):
        glow(c, x, y, r * 1.1, "#FFFFFF", z, 0.35)
        kit.disc(c, kit.flat("#FFFFFF"), x, y, r * 0.35, z, "snow")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, kit.gradient(["#B9A8C4", "#F2D6E8", "#B9A8C4"], w / 2, 0.7, axis="X"), kit.capsule_pts(x, y, w, 0.16),
                     z, "fog")

    def bolt(self, c, x, y, s, z):
        glow(c, x, y, 0.55 * s, "#FFD29A", z, 0.4)
        kit.poly(c, kit.gradient(["#FF7E6B", "#FFE29A"], 0.4 * s), kit.bolt_pts(x, y, s, 1.15), z, "bolt")


kit.build(Lofi())
kit.save()
