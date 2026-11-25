# "Knitted / felt" skin: weather cut from felt and sewn on, with dashed
# running stitches around each piece. Fuzzy felt lit from the top left,
# casting small shadows.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_felt.py -- art/felt.blend

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup(samples=96, denoise=True)  # first, since it clears the scene and its materials
kit.lit(energy=2.6)
bpy.context.scene.view_settings.exposure = 0.05
bpy.data.lights["light"].angle = math.radians(15)

T = 0.035  # felt thickness
_mats = {}


def felt(color):
    if color in _mats:
        return _mats[color]
    m = bpy.data.materials.new("felt_" + color)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kit.srgb(color)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Sheen Weight"].default_value = 0.8
    # Fibres: very fine, busy noise as a strong bump.
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0
    nz.inputs["Detail"].default_value = 12.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = kit.srgb(color)
    _mats[color] = m
    return m


def thread(color):
    key = "thread_" + color
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kit.srgb(color)
    b.inputs["Roughness"].default_value = 0.7
    m.diffuse_color = kit.srgb(color)
    _mats[key] = m
    return m


def piece(c, pts, color, z, stitch="#FFF8E7", inset=None):
    """A felt cut-out with running stitches just inside its edge."""
    o = kit.poly(c, felt(color), pts, z, "felt")
    so = o.modifiers.new("thick", "SOLIDIFY")
    so.thickness = T
    so.offset = 1.0
    bv = o.modifiers.new("soft", "BEVEL")
    bv.width = T * 0.4
    bv.segments = 3
    if stitch and len(pts) > 3:
        inner = inset if inset is not None else kit.grow_pts(pts, 0.86)
        kit.dashed(c, thread(stitch), inner, 0.012, 0.035, 0.025, z + T + 0.004)
    return o


class Felt(kit.Style):
    def sun(self, c, x, y, s, z):
        for i in range(10):
            a = 2 * math.pi * i / 10
            piece(c, kit.capsule_pts(x + 0.66 * s * math.cos(a), y + 0.66 * s * math.sin(a), 0.22 * s, 0.1 * s, a),
                  "#D9622B", z, None)
        piece(c, kit.circle_pts(x, y, 0.5 * s), "#E8A33D", z + 0.05)

    def moon(self, c, x, y, s, z):
        r = 0.55 * s
        piece(c, kit.crescent_pts(x, y, r), "#F3E6C4", z, "#8A6E4B",
              kit.crescent_pts(x - 0.035 * s, y - 0.03 * s, r * 0.85, 0.86, 0.55, 0.4))

    def star(self, c, x, y, r, z):
        piece(c, kit.star_pts(x, y, r * 1.4, 5, 0.5), "#F2C14E", z, None)

    def cloud(self, c, x, y, s, z, dark):
        col, st = ("#8C8F99", "#F4F1EA") if dark else ("#F4F1EA", "#7A8590")
        piece(c, kit.cloud_outline(x, y, s), col, z, st, kit.cloud_outline(x, y + 0.02 * s, s, 0.86))

    def raindrop(self, c, x, y, z):
        piece(c, kit.drop_pts(x, y, 0.09, 0.25), "#4A86C5", z, None)

    def drizzle(self, c, x, y, z):
        piece(c, kit.circle_pts(x, y, 0.05, 32), "#4A86C5", z, None)

    def flake(self, c, x, y, r, z):
        for i, arm in enumerate(kit.flake_arms(x, y, r * 1.15, 0.06)):
            piece(c, arm, "#FFFFFF", z + i * 0.04, None)

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            piece(c, kit.capsule_pts(x, y, w, 0.18), "#A9AEB6" if i % 2 else "#C9CCD1", z, "#FFFFFF",
                  kit.capsule_pts(x, y, w - 0.08, 0.1))

    def bolt(self, c, x, y, s, z):
        piece(c, kit.bolt_pts(x, y, s, 1.2), "#F2C14E", z, "#8A5A1E", kit.bolt_pts(x, y, s, 0.85))


kit.build(Felt())
kit.save()
