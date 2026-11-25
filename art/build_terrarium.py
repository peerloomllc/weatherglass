# "Terrarium" skin: each weather in its own little glass jar, with moss,
# pebbles and a sprout at the bottom. The jar is in every picture; the
# weather is drawn smaller to fit inside it.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_terrarium.py -- art/terrarium.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

K, OY = 0.52, 0.12  # weather scale and lift inside the jar (see kit.Plain)


def rounded_rect(x0, y0, x1, y1, r, steps=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for i in range(steps + 1):
            a = math.radians(a0 + 90 * i / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def leaf(x, y, length, width, angle):
    pts = []
    for i in range(25):
        t = i / 24
        pts.append((length * t, width * math.sin(math.pi * t)))
    for i in range(23, 0, -1):
        t = i / 24
        pts.append((length * t, -width * 0.4 * math.sin(math.pi * t)))
    ca, sa = math.cos(angle), math.sin(angle)
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]


def jar():
    b = kit.coll("base")
    body = rounded_rect(-0.7, -1.02, 0.7, 0.84, 0.32)
    kit.poly(b, kit.flat("#E3F1E8", 0.45), body, -0.5, "glass_back")
    kit.poly(b, kit.flat("#6B4A2F"), rounded_rect(-0.64, -0.96, 0.64, -0.66, 0.26), 0.6, "soil")
    for i, (x, r) in enumerate(((-0.5, 0.11), (-0.32, 0.14), (-0.12, 0.1), (0.08, 0.13), (0.3, 0.1), (0.5, 0.11))):
        kit.disc(b, kit.flat("#5E9E52" if i % 2 else "#7DB86A"), x, -0.68, r, 0.6, "moss")
    for x, r in ((-0.2, 0.05), (0.18, 0.04), (0.42, 0.045)):
        kit.disc(b, kit.flat("#A9A59C"), x, -0.86, r, 0.6, "pebble")
    kit.stroke(b, kit.flat("#4E8A43"), [(0.38, -0.68), (0.4, -0.52), (0.37, -0.4)], 0.025, 0.6, False, "stem")
    kit.poly(b, kit.flat("#7DB86A"), leaf(0.38, -0.46, 0.18, 0.07, math.radians(30)), 0.6, "leaf")
    kit.poly(b, kit.flat("#5E9E52"), leaf(0.38, -0.5, 0.16, 0.06, math.radians(155)), 0.6, "leaf")
    kit.poly(b, kit.flat("#C49A6C"), rounded_rect(-0.44, 0.84, 0.44, 1.02, 0.05), 0.6, "lid")
    for yy in (0.89, 0.97):
        kit.stroke(b, kit.flat("#9C7449"), [(-0.38, yy), (0.38, yy)], 0.012, 0.6, False, "cork")
    kit.stroke(b, kit.flat("#7FA391"), body, 0.035, 0.8, True, "glass")
    kit.stroke(b, kit.flat("#FFFFFF", 0.75), [(-0.58, 0.45), (-0.6, 0.1), (-0.58, -0.2)], 0.035, 0.8, False, "shine")
    kit.stroke(b, kit.flat("#FFFFFF", 0.6), [(-0.48, 0.62), (-0.42, 0.68)], 0.03, 0.8, False, "shine")


jar()
kit.build(kit.Plain(K, OY))
kit.save()
