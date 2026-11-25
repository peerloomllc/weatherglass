# "Round gauge" skin: a weather station dial. Colored zones run round the
# top from fair (right) through change to rain and storm (left), a red
# pointer marks the current weather, and its symbol sits in the middle.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_gauge.py -- art/gauge.blend
#
# The dial is in every picture. The pointer lives in the collection that
# only that weather's picture uses (sun, moon, cloud_small, cloud_big, fog,
# drizzle, rain, sleet, snow, bolt), so each picture shows one pointer.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

# Where the pointer sits: 1 is fair (right), -1 is storm (left).
POINT = {"sun": 1.0, "moon": 1.0, "cloud_small": 0.6, "cloud_big": 0.25, "fog": 0.05, "drizzle": -0.2,
         "rain": -0.45, "sleet": -0.6, "snow": -0.75, "bolt": -0.95}
ZONES = [(10, 60, "#F2C14E"), (60, 100, "#B9C0C8"), (100, 140, "#5E8FC4"), (140, 170, "#7A5BA6")]


def angle(p):
    return math.radians(90 - p * 75)


def dial():
    b = kit.coll("base")
    kit.disc(b, kit.gradient(["#5A5F66", "#D9DCE0", "#8C9198"], 1.06), 0, 0, 1.06, -0.6, "bezel")
    kit.disc(b, kit.flat("#F2EEE6"), 0, 0, 0.97, -0.55, "face")
    for a0, a1, col in ZONES:
        kit.poly(b, kit.flat(col), kit.ring_pts(0, 0, 0.93, 0.82, math.radians(a0), math.radians(a1), 24), -0.5, "zone")
    for i in range(17):
        a = math.radians(10 + i * 10)
        long = i % 2 == 0
        r0 = 0.74 if long else 0.77
        kit.stroke(b, kit.flat("#2A2F38"), [(r0 * math.cos(a), r0 * math.sin(a)), (0.81 * math.cos(a), 0.81 * math.sin(a))],
                   0.018 if long else 0.01, -0.5, False, "tick")


def pointer(c, p):
    a = angle(p)
    ca, sa = math.cos(a), math.sin(a)
    tip = (0.95 * ca, 0.95 * sa)
    l = (0.68 * ca - 0.06 * sa, 0.68 * sa + 0.06 * ca)
    r = (0.68 * ca + 0.06 * sa, 0.68 * sa - 0.06 * ca)
    kit.poly(c, kit.flat("#000000", 0.25), [(x + 0.02, y - 0.02) for x, y in (l, tip, r)], 0.9, "pointer_shadow")
    kit.poly(c, kit.flat("#C8102E"), [l, tip, r], 0.95, "pointer")


class Gauge(kit.Plain):
    """Plain symbols in the middle of the dial, plus each picture's pointer."""

    def __init__(self):
        super().__init__(0.5, -0.14)
        self.done = set()

    def mark(self, c):
        if c.name in POINT and c.name not in self.done:
            self.done.add(c.name)
            pointer(c, POINT[c.name])

    def sun(self, c, *a):
        self.mark(c)
        super().sun(c, *a)

    def moon(self, c, *a):
        self.mark(c)
        super().moon(c, *a)

    def cloud(self, c, *a):
        self.mark(c)
        super().cloud(c, *a)

    def raindrop(self, c, *a):
        self.mark(c)
        super().raindrop(c, *a)

    def drizzle(self, c, *a):
        self.mark(c)
        super().drizzle(c, *a)

    def flake(self, c, *a):
        self.mark(c)
        super().flake(c, *a)

    def fog(self, c, *a):
        self.mark(c)
        super().fog(c, *a)

    def bolt(self, c, *a):
        self.mark(c)
        super().bolt(c, *a)


dial()
kit.build(Gauge())
kit.save()
