# "Laser eyes" skin (Bitcoin group): bold cartoon weather where the sun, the
# moon and the clouds have glowing red laser eyes, after the Bitcoin meme.
# Each beam hangs off an empty named "laser..." placed at its eye and turned
# along the beam, so the opening clip (animate_clip.py, style "laser") can
# fire the beams out of the eyes.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_laser.py -- art/laser.blend

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup()  # first, since it clears the scene and its materials

LINE = "#141414"
BEAM_Z = 0.6  # beams go over everything


def beam(c, x, y, angle, length, width):
    """A laser beam from the eye at (x, y): a soft red glow, a red core and a
    white-hot middle, widening a little as it goes."""
    e = bpy.data.objects.new("laser", None)
    e.location = (x, y, BEAM_Z)
    e.rotation_euler = (0, 0, angle)
    c.objects.link(e)
    bpy.context.view_layer.update()
    for col, alpha, k in (("#FF4A4A", 0.35, 2.6), ("#FF1E1E", 1.0, 1.0), ("#FFE0E0", 1.0, 0.35)):
        w0, w1 = width * k * 0.6, width * k
        pts = [(0, -w0 / 2), (length, -w1 / 2), (length, w1 / 2), (0, w0 / 2)]
        ca, sa = math.cos(angle), math.sin(angle)
        o = kit.poly(c, kit.flat(col, alpha), [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts],
                     BEAM_Z, "beam")
        o.parent = e
        o.matrix_parent_inverse = e.matrix_world.inverted()


def eyes(c, x, y, s, z, length=1.0):
    """Two glowing eyes at (x +- d, y), each firing a beam outward."""
    d = 0.17 * s
    for side in (-1, 1):
        ex = x + side * d
        kit.disc(c, kit.flat("#FF4A4A", 0.45), ex, y, 0.13 * s, z, "glow")
        kit.disc(c, kit.flat("#FF1E1E"), ex, y, 0.08 * s, z, "eye")
        kit.disc(c, kit.flat("#FFFFFF"), ex, y, 0.035 * s, z, "eye")
        a = math.radians(90 - side * 58)  # out to each side and up
        beam(c, ex, y, a, length * s, 0.07 * s)


class Laser(kit.Plain):
    def __init__(self):
        super().__init__(1.0, outline=LINE, ow=0.03)

    def sun(self, c, x, y, s, z):
        super().sun(c, x, y, s, z)
        if s > 1:  # only the big sun; the small one sits behind a cloud
            eyes(c, x, y + 0.05 * s, s, z)
            kit.stroke(c, kit.flat(LINE), [(x - 0.12 * s, y - 0.17 * s), (x, y - 0.21 * s), (x + 0.13 * s, y - 0.15 * s)],
                       0.035, z, False, "smirk")

    def moon(self, c, x, y, s, z):
        super().moon(c, x, y, s, z)
        if s > 1:
            eyes(c, x - 0.24 * s, y - 0.12 * s, s * 0.8, z)

    def cloud(self, c, x, y, s, z, dark):
        super().cloud(c, x, y, s, z, dark)
        eyes(c, x - 0.04 * s, y + 0.02 * s, s * 0.85, z)

    def bolt(self, c, x, y, s, z):
        # The Lightning logo colors: a white bolt on a dark disc.
        kit.disc(c, kit.flat(LINE), x + 0.02, y - 0.02, 0.36 * s, z, "badge")
        kit.disc(c, kit.flat("#F7931A"), x + 0.02, y - 0.02, 0.32 * s, z, "badge")
        self.fill(c, "#FFFFFF", kit.bolt_pts(x, y, s * 0.85, 1.2), z, "bolt")


kit.build(Laser())
kit.save()
