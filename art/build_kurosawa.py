# "Kurosawa" skin: a black and white samurai film still. Grey silhouettes
# with film grain, long streaks of heavy rain, and a red sun as the only
# color.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_kurosawa.py -- art/kurosawa.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

G = 0.3  # film grain strength
GS = 70.0  # film grain size (bigger number, finer grain)


def f(color, alpha=1.0):
    return kit.flat(color, alpha, grain=G, grain_scale=GS)


class Kurosawa(kit.Style):
    def sun(self, c, x, y, s, z):
        kit.disc(c, f("#C8102E"), x, y, 0.62 * s, z, "sun")

    def moon(self, c, x, y, s, z):
        kit.disc(c, kit.radial("#ECE8E0", "#A8A39B"), x, y, 0.58 * s, z, "moon", unit=True)

    def star(self, c, x, y, r, z):
        kit.disc(c, f("#ECE8E0"), x, y, r * 0.35, z, "star")

    def cloud(self, c, x, y, s, z, dark):
        back, front = ("#3A3734", "#6E6A64") if dark else ("#6E6A64", "#BDB8B0")
        kit.cloud_flat(c, f(back), x, y, s, z, grow=1.08, dx=0.05, dy=-0.04)
        # Front layer has streaky grain, like a cloud painted on a backdrop.
        kit.cloud_flat(c, kit.flat(front, grain=0.35, grain_scale=30, stretch=8), x, y, s, z + 0.01)

    def raindrop(self, c, x, y, z):
        # Three long thin streaks per drop position: heavy driving rain.
        for dx, dy, ln in ((0, 0, 0.46), (0.1, 0.14, 0.32), (-0.08, 0.16, 0.24)):
            kit.poly(c, f("#ECE8E0", 0.92), kit.capsule_pts(x + dx, y + dy, ln, 0.026, math.radians(78)), z, "streak")

    def drizzle(self, c, x, y, z):
        kit.poly(c, f("#ECE8E0", 0.8), kit.capsule_pts(x, y, 0.16, 0.024, math.radians(78)), z, "streak")

    def flake(self, c, x, y, r, z):
        kit.disc(c, f("#ECE8E0"), x, y, r * 0.42, z, "snow")

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            kit.poly(c, f("#8A8680" if i % 2 else "#BDB8B0", 0.75), kit.capsule_pts(x, y, w, 0.16), z + i * 0.01, "fog")

    def bolt(self, c, x, y, s, z):
        kit.poly(c, f("#ECE8E0"), kit.bolt_pts(x, y, s, 1.1), z, "bolt")


kit.setup()
kit.build(Kurosawa())
kit.save()
