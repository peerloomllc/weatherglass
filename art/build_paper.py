# Build the starter "Paper cut" skin scene and save it as art/paper.blend.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_paper.py -- art/paper.blend
#
# Everything is flat cut-paper shapes stacked in thin layers, seen from
# above, lit from the top left so each layer casts a small shadow on the one
# below. A shadow catcher keeps those shadows on a transparent background.
#
# This only makes a starting point. Open paper.blend in Blender and reshape,
# recolor or replace anything by hand; keep the collection names, since
# render_skin.py uses them to pick what each weather picture shows.

import math
import sys

import bmesh
import bpy

D = 0.035  # thickness of one paper layer
GAP = 0.012  # air between layers, so shadows show

# Paper cut skin palette (matches the app's Paper cut colors)
C = {
    "sun": "#E3A33B", "sun_in": "#F2C766", "sun_rays": "#C4623A",
    "moon": "#F1E3C2", "moon_back": "#CDB892", "star": "#E9B949",
    "cloud": "#FBF6EC", "cloud_back": "#D9C8AC",
    "dark": "#9C8A74", "dark_back": "#6E5C48",
    "rain": "#5E8AA6", "rain_back": "#3F6680",
    "snow": "#FFFFFF", "snow_back": "#BFD3DF",
    "fog": "#E7DCC7", "fog2": "#D3C3A7",
    "bolt": "#E9B949", "bolt_back": "#C4623A",
}


def srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


_mats = {}


def mat(key):
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new("paper_" + key)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(C[key])
    bsdf.inputs["Roughness"].default_value = 0.95
    # Paper fibre: fine noise as a light bump.
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 260.0
    noise.inputs["Detail"].default_value = 8.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    _mats[key] = m
    return m


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def finish(obj, key, c):
    obj.data.materials.append(mat(key))
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    c.objects.link(obj)
    bev = obj.modifiers.new("edge", "BEVEL")
    bev.width = 0.006
    bev.segments = 2
    return obj


def layer_z(n, sub=0):
    # Shapes on the same layer that overlap must not share a top face, or
    # Cycles shades the overlap black. "sub" lifts each one a hair.
    return 0.06 + n * (D + GAP) + sub * 0.002


def disc(c, key, x, y, r, n, name="disc", sub=0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=D, location=(x, y, layer_z(n, sub)))
    o = bpy.context.active_object
    o.name = name
    return finish(o, key, c)


def poly(c, key, pts, n, name="shape", sub=0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, -D / 2)) for x, y in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, D), verts=top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location.z = layer_z(n, sub)
    bpy.context.scene.collection.objects.link(o)
    return finish(o, key, c)


def capsule(c, key, x, y, w, h, n, name="strip", sub=0):
    # A rounded strip: two half circles joined by straight sides.
    r = h / 2
    pts = []
    for i in range(17):
        a = math.pi / 2 + math.pi * i / 16
        pts.append((x - w / 2 + r + r * math.cos(a), y + r * math.sin(a)))
    for i in range(17):
        a = -math.pi / 2 + math.pi * i / 16
        pts.append((x + w / 2 - r + r * math.cos(a), y + r * math.sin(a)))
    return poly(c, key, pts, n, name, sub)


def drop(c, key, x, y, r, n, tilt=0.35):
    # Teardrop: circle with a tip pointing up and slightly right.
    tip = (x + r * 2.4 * math.sin(tilt), y + r * 2.4 * math.cos(tilt))
    dx, dy = tip[0] - x, tip[1] - y
    d = math.hypot(dx, dy)
    t = math.atan2(dy, dx)
    a = math.acos(r / d)
    pts = [tip]
    steps = 24
    for i in range(steps + 1):
        ang = t + a + (2 * math.pi - 2 * a) * i / steps
        pts.append((x + r * math.cos(ang), y + r * math.sin(ang)))
    return poly(c, key, pts, n, "drop")


def star(c, key, x, y, r, n, points=4, inner=0.38):
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.pi / 2 + math.pi * i / points
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return poly(c, key, pts, n, "star")


def flake(c, key, x, y, r, n):
    for i in range(3):
        a = math.pi / 2 + i * math.pi / 3
        w = 0.035
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa * w / 2, ca * w / 2
        pts = [(x - ca * r + px, y - sa * r + py), (x + ca * r + px, y + sa * r + py),
               (x + ca * r - px, y + sa * r - py), (x - ca * r - px, y - sa * r - py)]
        poly(c, key, pts, n, "flake", sub=i)


def sun(c, x, y, s, n0=0):
    rays = 12
    for i in range(rays):
        a = 2 * math.pi * i / rays
        base, tipr, half = 0.5 * s, 0.86 * s, 0.11 * s
        pts = [
            (x + base * math.cos(a - half / base * 1.0), y + base * math.sin(a - half / base * 1.0)),
            (x + tipr * math.cos(a), y + tipr * math.sin(a)),
            (x + base * math.cos(a + half / base * 1.0), y + base * math.sin(a + half / base * 1.0)),
        ]
        poly(c, "sun_rays", pts, n0, "ray")
    disc(c, "sun", x, y, 0.55 * s, n0 + 1, "sun")
    disc(c, "sun_in", x, y, 0.38 * s, n0 + 2, "sun_in")


def moon(c, x, y, s, n0=0):
    # Crescent: a disc with a second disc cut out of it.
    for key, grow, n in (("moon_back", 1.06, n0), ("moon", 1.0, n0 + 1)):
        o = disc(c, key, x, y, 0.6 * s * grow, n, "moon")
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.5 * s, depth=1.0,
                                            location=(x + 0.3 * s, y + 0.22 * s, 0))
        cut = bpy.context.active_object
        cut.name = "moon_cut"
        cut.hide_render = True
        cut.hide_viewport = True
        for uc in list(cut.users_collection):
            uc.objects.unlink(cut)
        c.objects.link(cut)
        b = o.modifiers.new("cut", "BOOLEAN")
        b.operation = "DIFFERENCE"
        b.object = cut
        o.modifiers.move(len(o.modifiers) - 1, 0)


CLOUD = [(-0.47, -0.08, 0.3), (-0.12, 0.14, 0.4), (0.3, 0.02, 0.33), (0.02, -0.12, 0.3)]


def cloud(c, top, back, x, y, s, n0=0):
    for key, grow, dx, dy, n in ((back, 1.08, 0.02, -0.03, n0), (top, 1.0, 0, 0, n0 + 1)):
        for i, (cx, cy, r) in enumerate(CLOUD):
            disc(c, key, x + (cx + dx) * s, y + (cy + dy) * s, r * s * grow, n, "puff", sub=i + 1)
        capsule(c, key, x + dx * s, y + (-0.2 + dy) * s, 1.32 * s * grow, 0.36 * s * grow, n, "base")


def bolt(c, x, y, s, n0):
    pts = [(0.06, 0.32), (-0.2, -0.04), (-0.02, -0.04), (-0.14, -0.42), (0.22, 0.06), (0.04, 0.06), (0.16, 0.32)]
    for key, grow, n in (("bolt_back", 1.12, n0), ("bolt", 1.0, n0 + 1)):
        poly(c, key, [(x + px * s * grow, y + py * s * grow) for px, py in pts], n, "bolt")


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Render settings: Cycles on the GPU, small square transparent PNGs.
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dev_type in ("OPTIX", "CUDA", "HIP", "METAL"):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            if any(d.type == dev_type for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == dev_type
                scene.cycles.device = "GPU"
                break
        except TypeError:
            continue
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = -0.7

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    scene.world = world

    base = coll("base")
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.25
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0, 0, 5)
    base.objects.link(cam)
    scene.camera = cam

    sun_data = bpy.data.lights.new("light", "SUN")
    sun_data.energy = 2.2
    sun_data.angle = math.radians(6)
    light = bpy.data.objects.new("light", sun_data)
    light.rotation_euler = (math.radians(-28), math.radians(-24), 0)
    base.objects.link(light)

    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    catcher = bpy.context.active_object
    catcher.name = "shadow_catcher"
    catcher.is_shadow_catcher = True
    for uc in list(catcher.users_collection):
        uc.objects.unlink(catcher)
    base.objects.link(catcher)

    # One collection per weather element (names are the contract with
    # render_skin.py).
    sun(coll("sun"), 0, 0, 1.15)
    sun(coll("sun_small"), -0.33, 0.33, 0.78)
    moon(coll("moon"), 0.05, 0.02, 1.15)
    moon(coll("moon_small"), -0.3, 0.32, 0.8)
    st = coll("stars")
    for x, y, r in ((0.6, 0.55, 0.11), (0.72, 0.12, 0.07), (0.38, 0.78, 0.06), (-0.62, -0.6, 0.08)):
        star(st, "star", x, y, r, 0)
    cloud(coll("cloud_small"), "cloud", "cloud_back", 0.22, -0.2, 0.95, n0=3)
    cloud(coll("cloud_big"), "cloud", "cloud_back", 0, 0.02, 1.3)
    cloud(coll("cloud_top"), "cloud", "cloud_back", 0, 0.25, 1.2, n0=2)
    cloud(coll("cloud_dark_top"), "dark", "dark_back", 0, 0.25, 1.2, n0=2)

    rn = coll("rain")
    for x, y in ((-0.42, -0.5), (-0.05, -0.68), (0.32, -0.5), (0.12, -0.92), (-0.28, -0.88)):
        drop(rn, "rain_back", x + 0.012, y - 0.012, 0.098, 0)
        drop(rn, "rain", x, y, 0.09, 1)
    dz = coll("drizzle")
    for x, y in ((-0.4, -0.52), (-0.1, -0.7), (0.22, -0.55), (0.42, -0.78), (0.0, -0.95), (-0.3, -0.88)):
        disc(dz, "rain", x, y, 0.062, 0, "dot")
    sn = coll("snow")
    for x, y, r in ((-0.4, -0.55, 0.13), (0.05, -0.7, 0.15), (0.42, -0.55, 0.12), (-0.18, -0.95, 0.1), (0.28, -0.95, 0.1)):
        flake(sn, "snow_back", x + 0.012, y - 0.012, r * 1.3, 0)
        flake(sn, "snow", x, y, r * 1.25, 1)
    sl = coll("sleet")
    for x, y in ((-0.38, -0.55), (0.3, -0.62)):
        drop(sl, "rain_back", x + 0.012, y - 0.012, 0.098, 0)
        drop(sl, "rain", x, y, 0.09, 1)
    for x, y, r in ((-0.02, -0.78, 0.12), (-0.36, -0.98, 0.09), (0.36, -0.98, 0.09)):
        flake(sl, "snow_back", x + 0.012, y - 0.012, r * 1.3, 0)
        flake(sl, "snow", x, y, r * 1.25, 1)
    fg = coll("fog")
    for i, (x, y, w) in enumerate(((-0.1, 0.48, 1.4), (0.12, 0.16, 1.6), (-0.08, -0.16, 1.5), (0.1, -0.48, 1.3))):
        capsule(fg, "fog2" if i % 2 else "fog", x, y, w, 0.2, i, "fog")
    bolt(coll("bolt"), 0.02, -0.62, 1.0, n0=0)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
build()
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(argv[0]) if argv else "paper.blend")
print("SAVED")
