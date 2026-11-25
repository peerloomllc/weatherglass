# "Claymation" skin: weather modelled in modelling clay. Rounded, slightly
# lumpy shapes with a fine fingerprint texture, lit from the top left and
# casting soft shadows.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_clay.py -- art/clay.blend
#
# Each shape is built as a rough solid, then a Remesh and a Smooth modifier
# round every edge the way clay rounds, and a Displace modifier adds lumps.
# In Blender you can sculpt or reshape any of them by hand.

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup(samples=96, denoise=True)  # first, since it clears the scene and its materials
kit.lit(energy=3.0)
bpy.context.scene.view_settings.exposure = -0.25
bpy.data.lights["light"].angle = math.radians(25)  # softer shadows

_mats = {}


def clay(color):
    if color in _mats:
        return _mats[color]
    m = bpy.data.materials.new("clay_" + color)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kit.srgb(color)
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Subsurface Weight"].default_value = 0.15
    # Fingerprints and tool marks: fine noise as a light bump.
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 90.0
    nz.inputs["Detail"].default_value = 4.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = kit.srgb(color)
    _mats[color] = m
    return m


_lumps = []


def lumps():
    if not _lumps:
        t = bpy.data.textures.new("lumps", "CLOUDS")
        t.noise_scale = 0.18
        _lumps.append(t)
    return _lumps[0]


def finish(bm, c, color, name, voxel=0.012, z=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location.z = z
    c.objects.link(o)
    o.data.materials.append(clay(color))
    rm = o.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    sm = o.modifiers.new("round", "SMOOTH")
    sm.factor = 1.0
    sm.iterations = 12
    dp = o.modifiers.new("lumps", "DISPLACE")
    dp.texture = lumps()
    dp.strength = 0.012
    dp.mid_level = 0.5
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def add_slab(bm, pts, depth, z0=0.0):
    vs = [bm.verts.new((x, y, z0)) for x, y in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def add_ball(bm, x, y, r, squash=0.6, z0=0.0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    bmesh.ops.scale(bm, vec=(1, 1, squash), verts=res["verts"])
    bmesh.ops.translate(bm, vec=(x, y, z0 + r * squash), verts=res["verts"])


def slab(c, color, pts, z, depth=0.1, name="clay", voxel=0.012):
    bm = bmesh.new()
    add_slab(bm, pts, depth)
    return finish(bm, c, color, name, voxel, z)


class Clay(kit.Style):
    def sun(self, c, x, y, s, z):
        for i in range(10):
            a = 2 * math.pi * i / 10
            slab(c, "#F28C28", kit.capsule_pts(x + 0.68 * s * math.cos(a), y + 0.68 * s * math.sin(a), 0.22 * s, 0.1 * s, a),
                 z, 0.06, "ray", 0.008)
        bm = bmesh.new()
        add_ball(bm, x, y, 0.48 * s, 0.35)
        finish(bm, c, "#F7B733", "sun", 0.012, z)

    def moon(self, c, x, y, s, z):
        slab(c, "#F3E3A0", kit.crescent_pts(x, y, 0.55 * s), z, 0.14, "moon")

    def star(self, c, x, y, r, z):
        slab(c, "#F7D354", kit.star_pts(x, y, r * 1.4, 5, 0.5), z, 0.05, "star", 0.006)

    def cloud(self, c, x, y, s, z, dark):
        circles, base = kit.cloud_shapes(x, y, s)
        bm = bmesh.new()
        for cx, cy, r in circles:
            add_ball(bm, cx, cy, r, 0.45)
        add_slab(bm, base, 0.16 * s)
        finish(bm, c, "#7D8597" if dark else "#F2F0EB", "cloud", 0.014, z)

    def raindrop(self, c, x, y, z):
        slab(c, "#3E8EDE", kit.drop_pts(x, y, 0.09, 0.25), z, 0.07, "drop", 0.007)

    def drizzle(self, c, x, y, z):
        bm = bmesh.new()
        add_ball(bm, x, y, 0.05, 0.7)
        finish(bm, c, "#3E8EDE", "drop", 0.006, z)

    def flake(self, c, x, y, r, z):
        bm = bmesh.new()
        for arm in kit.flake_arms(x, y, r * 1.15, 0.06):
            add_slab(bm, arm, 0.05)
        finish(bm, c, "#FFFFFF", "flake", 0.006, z)

    def fog(self, c, bars, z):
        for i, (x, y, w) in enumerate(bars):
            bm = bmesh.new()
            add_slab(bm, kit.capsule_pts(x, y, w, 0.16), 0.1)
            finish(bm, c, "#B8BDC6" if i % 2 else "#D3D6DC", "fog", 0.012, z)

    def bolt(self, c, x, y, s, z):
        slab(c, "#FFD23F", kit.bolt_pts(x, y, s, 1.2), z, 0.08, "bolt", 0.008)


kit.build(Clay())
kit.save()
