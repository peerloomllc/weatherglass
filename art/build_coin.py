# "Orange coin" skin (Bitcoin group): each weather symbol stamped on a shiny
# orange Bitcoin coin with a dark inlaid face. The coin is in every picture;
# the weather is drawn smaller on its face. The opening clip spins the coin
# with the Bitcoin sign on it before the weather appears (animate_clip.py,
# style "coin").
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_coin.py -- art/coin.blend

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

R = 1.05  # coin radius
FACE = 0.78  # inlaid face radius


def coin():
    b = kit.coll("base")
    kit.disc(b, kit.flat("#000000", 0.28), 0.05, -0.06, R, -0.7, "shadow")
    # Rim: a darker edge, the orange coin, a light shine across the top left.
    kit.disc(b, kit.flat("#B8650A"), 0, 0, R, -0.6, "edge")
    kit.disc(b, kit.radial("#FFB547", "#F7931A"), 0, 0, R * 0.95, -0.55, "rim", unit=True)
    kit.poly(b, kit.flat("#FFFFFF", 0.35), kit.ring_pts(0, 0, R * 0.93, R * 0.86, math.radians(100), math.radians(170)),
             -0.5, "shine")
    # Reeded ticks between the rim and the face.
    for i in range(36):
        a = 2 * math.pi * i / 36
        kit.poly(b, kit.flat("#C4700C"), kit.capsule_pts(0.84 * math.cos(a), 0.84 * math.sin(a), 0.05, 0.022, a),
                 -0.5, "tick")
    # The dark inlaid face, with a thin orange line round it.
    kit.disc(b, kit.flat("#E07F0F"), 0, 0, FACE + 0.025, -0.48, "lip")
    kit.disc(b, kit.radial("#2A2118", "#15110C"), 0, 0, FACE, -0.46, "face", unit=True)


coin()
kit.build(kit.Plain(0.5, 0.0, outline="#0E0A06", ow=0.016))
kit.save()
