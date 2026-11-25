# "Isometric town" skin: a tiny 3D town block (grass, a house and two
# trees) seen from above at an angle, with the weather floating over it.
# The town is in every picture; the weather symbols face the camera.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_iso.py -- art/iso.blend
#
# The town is ordinary lit 3D, so in Blender you can add buildings or move
# things around. The weather symbols are flat shapes parented to the
# "weather" empty, which turns them toward the camera.

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

kit.setup(samples=96, denoise=True)  # first, since it clears the scene and its materials
kit.lit(energy=3.4)
scene = bpy.context.scene
scene.view_settings.exposure = 0.15

# Isometric camera: looking down at about 35 degrees from the south-east.
cam = scene.camera
cam.location = Vector((6, -6, 6))
cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.ortho_scale = 2.5
cam.data.shift_y = 0.1

_mats = {}


def mat(color, rough=0.8):
    if color in _mats:
        return _mats[color]
    m = bpy.data.materials.new("town_" + color)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = kit.srgb(color)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = kit.srgb(color)
    _mats[color] = m
    return m


def obj(op, color, loc, scale=(1, 1, 1), rot=(0, 0, 0), smooth=False, **kw):
    op(location=loc, rotation=rot, **kw)
    o = bpy.context.active_object
    o.scale = scale
    o.data.materials.append(mat(color))
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    kit.coll("base").objects.link(o)
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    bv = o.modifiers.new("soft", "BEVEL")
    bv.width = 0.012
    bv.segments = 2
    return o


def town():
    cube = bpy.ops.mesh.primitive_cube_add
    obj(cube, "#8A5A3B", (0, 0, -0.16), (0.46, 0.46, 0.1))  # dirt
    obj(cube, "#7DBE5A", (0, 0, -0.04), (0.46, 0.46, 0.03))  # grass
    obj(cube, "#D9C9A3", (0.12, -0.24, 0.0), (0.08, 0.22, 0.012))  # path
    # House: walls, a pitched roof, a door and a chimney.
    obj(cube, "#F2E6D0", (0.1, 0.1, 0.12), (0.16, 0.13, 0.12))
    roof = obj(bpy.ops.mesh.primitive_cylinder_add, "#C8553D", (0.1, 0.1, 0.3), (0.13, 0.12, 0.19), (0, math.pi / 2, 0),
               vertices=3)
    roof.rotation_euler = (0, math.pi / 2, 0)
    obj(cube, "#7A4A2E", (0.12, -0.035, 0.07), (0.035, 0.006, 0.06))  # door
    obj(cube, "#9C8E80", (0.18, 0.15, 0.38), (0.025, 0.025, 0.06))  # chimney
    # Two trees.
    for x, y, s in ((-0.28, -0.22, 1.0), (-0.26, 0.26, 0.8)):
        obj(bpy.ops.mesh.primitive_cylinder_add, "#7A4A2E", (x, y, 0.06 * s), (0.025 * s, 0.025 * s, 0.07 * s), vertices=12)
        obj(bpy.ops.mesh.primitive_ico_sphere_add, "#4E9A45", (x, y, 0.2 * s), (0.11 * s, 0.11 * s, 0.13 * s), smooth=True,
            subdivisions=2)


town()

# Weather: drawn flat by kit.Plain, then every shape is parented to an
# empty that faces the camera and floats above the town.
before = set(bpy.data.objects)
kit.build(kit.Plain(1.0))
made = set(bpy.data.objects) - before
rot = cam.rotation_euler.to_matrix()
up, toward = rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, 1))
holder = bpy.data.objects.new("weather", None)
holder.location = up * 0.95 + toward * 3
holder.rotation_euler = cam.rotation_euler
holder.scale = (0.5, 0.5, 0.5)
kit.coll("base").objects.link(holder)
for o in made:
    o.parent = holder
    o.visible_shadow = False  # the symbols should not shade the town
kit.save()
