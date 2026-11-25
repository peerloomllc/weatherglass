# "Risograph" skin: a two-ink print in fluorescent pink and blue on cream
# paper. Ink lies grainy and uneven, and the second ink is printed a little
# out of line with the first, so a sliver of it shows at one edge.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_riso.py -- art/riso.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

PINK, BLUE, YELLOW = "#FF48B0", "#0078BF", "#FFE800"
MIS = (0.024, -0.016)  # how far the second ink is out of line


def ink(color, alpha=0.92):
    return kit.flat(color, alpha, alpha_grain=0.2, grain_scale=70)


def two(c, pts, main, under, z, alpha=0.92):
    """Print "under" first, out of line, then "main" over it."""
    kit.poly(c, ink(under, 0.85), [(x + MIS[0], y + MIS[1]) for x, y in pts], z, "under")
    kit.poly(c, ink(main, alpha), pts, z, "main")


class Riso(kit.Style):
    def sun(self, c, x, y, s, z):
        for i in range(10):
            a = 2 * math.pi * i / 10
            kit.poly(c, ink(YELLOW), kit.capsule_pts(x + 0.66 * s * math.cos(a), y + 0.66 * s * math.sin(a), 0.2 * s, 0.08 * s, a),
                     z, "ray")
        two(c, kit.circle_pts(x, y, 0.48 * s), PINK, YELLOW, z)

    def moon(self, c, x, y, s, z):
        two(c, kit.crescent_pts(x, y, 0.55 * s), BLUE, PINK, z)

    def star(self, c, x, y, r, z):
        kit.poly(c, ink(PINK), kit.star_pts(x, y, r * 1.3, 4, 0.3), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        two(c, kit.cloud_outline(x, y, s), BLUE, PINK, z, 0.95 if dark else 0.5)

    def raindrop(self, c, x, y, z):
        kit.poly(c, ink(BLUE), kit.drop_pts(x, y, 0.085, 0.3), z, "drop")

    def drizzle(self, c, x, y, z):
        kit.disc(c, ink(BLUE), x, y, 0.045, z, "drop")

    def flake(self, c, x, y, r, z):
        for arm in kit.flake_arms(x, y, r * 1.15, 0.05):
            kit.poly(c, ink(PINK), arm, z, "flake")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, ink(BLUE if i % 2 else PINK, 0.75), kit.capsule_pts(x, y, w, 0.17), z, "fog")

    def bolt(self, c, x, y, s, z):
        two(c, kit.bolt_pts(x, y, s, 1.15), PINK, YELLOW, z)


kit.build(Riso())
kit.save()
