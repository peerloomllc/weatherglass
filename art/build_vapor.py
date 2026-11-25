# "Vaporwave" skin: pastel gradients in pink, purple and cyan, with a cyan
# and a pink copy of every shape knocked slightly out of line, like a
# glitchy 90s video.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_vapor.py -- art/vapor.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

PINK, CYAN, PURPLE, YELLOW, WHITE = "#FF71CE", "#01CDFE", "#B967FF", "#FFFB96", "#FFFFFF"
SPLIT = 0.03  # how far the colored copies sit out of line

LEFT = kit.flat(CYAN, 0.9)
RIGHT = kit.flat(PINK, 0.9)


def shifted(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def glitch(c, pts, m, z, k=1.0):
    kit.poly(c, LEFT, shifted(pts, -SPLIT * k, SPLIT * 0.4 * k), z, "cyan")
    kit.poly(c, RIGHT, shifted(pts, SPLIT * k, -SPLIT * 0.4 * k), z, "pink")
    kit.poly(c, m, pts, z, "shape")


class Vapor(kit.Style):
    def sun(self, c, x, y, s, z):
        r = 0.55 * s
        glitch(c, kit.circle_pts(x, y, r), kit.gradient([PINK, "#FF9E9E", YELLOW], r), z)

    def moon(self, c, x, y, s, z):
        r = 0.55 * s
        glitch(c, kit.crescent_pts(x, y, r), kit.gradient([PURPLE, "#E7D1FF"], r), z)

    def star(self, c, x, y, r, z):
        glitch(c, kit.star_pts(x, y, r * 1.3, 4, 0.25), kit.flat(WHITE), z, 0.5)

    def cloud(self, c, x, y, s, z, dark):
        cols = [PURPLE, "#D9B8FF"] if dark else ["#FFC6EC", WHITE]
        glitch(c, kit.cloud_outline(x, y, s), kit.gradient(cols, 0.32 * s), z)

    def raindrop(self, c, x, y, z):
        glitch(c, kit.drop_pts(x, y, 0.09, 0.3), kit.gradient([CYAN, "#C9F6FF"], 0.15), z, 0.6)

    def drizzle(self, c, x, y, z):
        glitch(c, kit.circle_pts(x, y, 0.055, 32), kit.flat("#7FE6FF"), z, 0.5)

    def flake(self, c, x, y, r, z):
        for arm in kit.flake_arms(x, y, r * 1.2, 0.055):
            glitch(c, arm, kit.flat(WHITE), z, 0.5)

    def fog(self, c, bars, z):
        for x, y, w in bars:
            glitch(c, kit.capsule_pts(x, y, w, 0.15), kit.gradient([PINK, PURPLE, CYAN], w / 2, axis="X"), z)

    def bolt(self, c, x, y, s, z):
        glitch(c, kit.bolt_pts(x, y, s, 1.15), kit.gradient(["#FFC93C", YELLOW], 0.4 * s), z)


kit.build(Vapor())
kit.save()
