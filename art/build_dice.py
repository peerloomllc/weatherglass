# "Tabletop dice" skin: each weather symbol printed on the face of a red
# twenty-sided die, like the dice on a tabletop game night. The die is in
# every picture; the weather is drawn smaller on its middle face.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_dice.py -- art/dice.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

R = 1.04  # die radius
LIGHT = (-0.6, 0.8)  # light comes from the top left


def tone(h, k):
    """Lighten (k > 0) or darken (k < 0) a hex color."""
    h = h.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    rgb = [round(c + (255 - c) * k) if k > 0 else round(c * (1 + k)) for c in rgb]
    return "#" + "".join(f"{min(255, max(0, c)):02X}" for c in rgb)


def die():
    b = kit.coll("base")
    H = {a: (R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in (30, 90, 150, 210, 270, 330)}
    T = {a: (0.56 * R * math.cos(math.radians(a)), 0.56 * R * math.sin(math.radians(a))) for a in (90, 210, 330)}
    faces = [
        (T[90], H[150], T[210]), (T[210], H[270], T[330]), (T[330], H[30], T[90]),
        (T[90], H[30], H[90]), (T[90], H[90], H[150]), (T[210], H[150], H[210]),
        (T[210], H[210], H[270]), (T[330], H[270], H[330]), (T[330], H[330], H[30]),
    ]
    base = "#B23A48"
    kit.poly(b, kit.flat("#000000", 0.25), [(H[a][0] + 0.05, H[a][1] - 0.06) for a in (30, 90, 150, 210, 270, 330)], -0.6,
             "shadow")
    for f in faces:
        cx, cy = sum(p[0] for p in f) / 3, sum(p[1] for p in f) / 3
        d = math.hypot(cx, cy)
        lit = (cx * LIGHT[0] + cy * LIGHT[1]) / d
        kit.poly(b, kit.flat(tone(base, 0.25 * lit if lit > 0 else 0.35 * lit)), list(f), -0.5, "facet")
    kit.poly(b, kit.flat(tone(base, 0.12)), [T[90], T[210], T[330]], -0.5, "face")
    for f in faces + [(T[90], T[210], T[330])]:
        kit.stroke(b, kit.flat("#F2A0AA", 0.7), list(f), 0.012, -0.45, True, "edge")


die()
kit.build(kit.Plain(0.47, 0.0, outline="#3B1A20", ow=0.018))
kit.save()
