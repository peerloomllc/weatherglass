# Build the starter "Retro-future" skin scene and save it as art/retro.blend.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_retro.py -- art/retro.blend
#
# A neon synthwave look to match the skin's purple, pink and cyan colors:
# a striped glowing sun, a glowing crescent moon, chrome clouds that reflect
# a pink and cyan sky, and neon rain, snow and lightning with a soft glow
# around them. Seen from above like the other skins.
#
# This only makes a starting point. Open retro.blend in Blender and reshape,
# recolor or replace anything by hand; keep the collection names, since
# render_skin.py uses them to pick what each weather picture shows.

import math
import sys

import bmesh
import bpy

C = {
    "sun_top": "#FFE45C", "sun_mid": "#FF9A3D", "sun_bot": "#FF3D8B",
    "sun_glow": "#FF5FA2",
    "moon": "#F9EAFF", "moon_edge": "#8FF4F6", "moon_glow": "#8FF4F6",
    "star": "#FFFFFF", "star_glow": "#2DE2E6", "star_glow2": "#FF5FA2",
    "cloud": "#EDE2FF", "dark": "#8A6AB8",
    "rain": "#2DE2E6", "snow": "#F4FDFF", "snow_glow": "#8FF4F6",
    "bolt_top": "#FFF27A", "bolt_bot": "#FF5FA2", "bolt_glow": "#FF5FA2",
    "fog": "#FF5FA2", "fog2": "#2DE2E6",
    "sky_up": "#FFF4FF", "sky_mid": "#C9A8FF", "sky_pink": "#FF5FA2", "sky_cyan": "#2DE2E6",
    "sky_down": "#1A0B2E",
}


def srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


# ---- materials -------------------------------------------------------------

_mats = {}


def _new(name):
    m = bpy.data.materials.new("retro_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    _mats[name] = m
    return m, nt, out


def emit(key, strength=1.0):
    name = f"emit_{key}_{strength}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(C[key])
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.diffuse_color = srgb(C[key])
    return m


def emit_ramp(name, keys, extent, strength=1.0):
    # Glowing color that changes from bottom to top: keys[0] at the bottom
    # (object y = -extent), keys[-1] at the top (y = +extent).
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -extent
    mr.inputs["From Max"].default_value = extent
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    while len(els) < len(keys):
        els.new(0.5)
    for i, k in enumerate(keys):
        els[i].position = i / (len(keys) - 1)
        els[i].color = srgb(C[k])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.diffuse_color = srgb(C[keys[-1]])
    return m


def _see_through(m, nt, out, fac_socket, color_key, strength):
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(C[color_key])
    em.inputs["Strength"].default_value = strength
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac_socket, mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.diffuse_color = srgb(C[color_key])


def glow(key, strength=1.0, power=2.4):
    # A soft round glow, strongest in the middle, gone at the rim. Used on a
    # disc of radius 1, scaled to size.
    name = f"glow_{key}_{strength}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.use_clamp = True
    inv.inputs[0].default_value = 1.0
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = power
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.use_clamp = True
    mul.inputs[1].default_value = strength
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    nt.links.new(ln.outputs["Value"], inv.inputs[1])
    nt.links.new(inv.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], mul.inputs[0])
    _see_through(m, nt, out, mul.outputs[0], key, 1.0)
    return m


def line_glow(key, half, radius, strength=0.6):
    # Soft glow around a neon line that runs along object x from -half to
    # half: strongest on the line, gone at "radius" away from it.
    name = f"lglow_{key}_{half}_{radius}_{strength}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = half
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mx.inputs[1].default_value = 0.0
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    dv.inputs[1].default_value = radius
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.use_clamp = True
    inv.inputs[0].default_value = 1.0
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.0
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], ab.inputs[0])
    nt.links.new(ab.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], mx.inputs[0])
    nt.links.new(mx.outputs[0], comb.inputs["X"])
    nt.links.new(sep.outputs["Y"], comb.inputs["Y"])
    nt.links.new(comb.outputs[0], ln.inputs[0])
    nt.links.new(ln.outputs["Value"], dv.inputs[0])
    nt.links.new(dv.outputs[0], inv.inputs[1])
    nt.links.new(inv.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], mul.inputs[0])
    _see_through(m, nt, out, mul.outputs[0], key, 1.0)
    return m


def fade_x(key, half, alpha=1.0):
    # Neon bar that fades out toward both ends (object x = -half..half).
    name = f"fade_{key}_{half}_{alpha}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    dv.inputs[1].default_value = half
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.0
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.use_clamp = True
    inv.inputs[0].default_value = 1.0
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["X"], ab.inputs[0])
    nt.links.new(ab.outputs[0], dv.inputs[0])
    nt.links.new(dv.outputs[0], pw.inputs[0])
    nt.links.new(pw.outputs[0], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = alpha
    nt.links.new(inv.outputs[0], mul.inputs[0])
    _see_through(m, nt, out, mul.outputs[0], key, 1.0)
    return m


def chrome(key, rough):
    name = f"chrome_{key}_{rough}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = srgb(C[key])
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.diffuse_color = srgb(C[key])
    return m


# ---- shapes ----------------------------------------------------------------

_glow_z = [-0.1]  # height of the next glow; see halo() and streak()


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def put(obj, m, c, smooth=False):
    obj.data.materials.append(m)
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    c.objects.link(obj)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def disc(c, m, x, y, r, z, depth=0.02, name="disc"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=depth, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    return put(o, m, c)


def halo(c, m, x, y, r):
    # Flat glow disc of radius 1, scaled, so the glow material sees 0..1.
    # Each sits a hair below the last so overlapping glows never share a
    # plane (Cycles shades that overlap black).
    _glow_z[0] -= 0.002
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=1.0, fill_type="NGON", location=(x, y, _glow_z[0] - 0.1))
    o = bpy.context.active_object
    o.name = "glow"
    o.scale = (r, r, 1)
    return put(o, m, c)


def poly(c, m, pts, z, depth=0.03, name="shape", bevel=0.0):
    # Points are relative to (0, 0); the object sits at their average so
    # gradients and fades in object space are centred on the shape.
    ax = sum(p[0] for p in pts) / len(pts)
    ay = sum(p[1] for p in pts) / len(pts)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x - ax, y - ay, -depth / 2)) for x, y in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (ax, ay, z)
    bpy.context.scene.collection.objects.link(o)
    if bevel:
        bv = o.modifiers.new("edge", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    return put(o, m, c)


def capsule_pts(x, y, w, h, angle=0.0):
    r = h / 2
    pts = []
    for i in range(13):
        a = math.pi / 2 + math.pi * i / 12
        pts.append((-w / 2 + r + r * math.cos(a), r * math.sin(a)))
    for i in range(13):
        a = -math.pi / 2 + math.pi * i / 12
        pts.append((w / 2 - r + r * math.cos(a), r * math.sin(a)))
    ca, sa = math.cos(angle), math.sin(angle)
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]


def cutter(c, loc, size):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = "cut"
    o.scale = size
    o.hide_render = True
    o.hide_viewport = True
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    c.objects.link(o)
    return o


def sun(c, x, y, r, slits=True):
    # The synthwave sun: yellow at the top fading to hot pink at the bottom,
    # with horizontal gaps across its lower half that get wider toward the
    # bottom.
    halo(c, glow("sun_glow", 0.85), x, y, r * 1.75)
    o = disc(c, emit_ramp("sun", ["sun_bot", "sun_mid", "sun_top"], r), x, y, r, 0.1, name="sun")
    if slits:
        for i, (fy, th) in enumerate(((-0.12, 0.05), (-0.34, 0.075), (-0.56, 0.1), (-0.78, 0.13))):
            cut = cutter(c, (x, y + fy * r, 0.1), (r * 2.4, th * r, 1.0))
            b = o.modifiers.new(f"slit{i}", "BOOLEAN")
            b.operation = "DIFFERENCE"
            b.object = cut


def moon(c, x, y, r):
    halo(c, glow("moon_glow", 0.3, power=3.0), x, y, r * 1.5)
    o = disc(c, emit_ramp("moon", ["moon_edge", "moon", "moon"], r), x, y, r, 0.1, name="moon")
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r * 0.82, depth=1.0,
                                        location=(x + r * 0.5, y + r * 0.36, 0))
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


def sparkle(c, x, y, r, glow_key):
    halo(c, glow(glow_key, 0.7), x, y, r * 1.8)
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.22
        a = math.pi / 2 + math.pi * i / 4
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    poly(c, emit("star", 1.0), pts, 0.1, name="star")


PUFFS = [(-0.47, -0.06, 0.3), (-0.12, 0.14, 0.4), (0.3, 0.02, 0.33), (0.02, -0.1, 0.3)]


def cloud(c, key, x, y, s, rough=0.16):
    m = chrome(key, rough)
    for cx, cy, r in PUFFS:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=r * s,
                                             location=(x + cx * s, y + cy * s, 0.3))
        o = bpy.context.active_object
        o.name = "puff"
        o.scale.z = 0.55
        put(o, m, c, smooth=True)
    base = poly(c, m, capsule_pts(x, y - 0.2 * s, 1.32 * s, 0.36 * s), 0.3, depth=0.2 * s,
                name="base", bevel=0.09 * s)
    for p in base.data.polygons:
        p.use_smooth = True


def streak(c, key, x, y, length, width, angle):
    # Neon line plus a soft glow. The glow is a flat rectangle turned to the
    # line's angle, so its material can measure distance along and across.
    rad = width * 3.0
    half = (length - width) / 2
    # Glows that overlap must not lie in the same plane, or Cycles shades
    # the overlap black. Each one sits a hair lower than the last.
    _glow_z[0] -= 0.002
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(x, y, _glow_z[0]))
    g = bpy.context.active_object
    g.name = "streak_glow"
    g.scale = (2 * (half + rad), 2 * rad, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    g.rotation_euler.z = angle
    put(g, line_glow(key, half, rad, 1.0), c)
    poly(c, emit(key, 1.0), capsule_pts(x, y, length, width, angle), 0.0, depth=0.01, name="streak")


def flake(c, x, y, r):
    halo(c, glow("snow_glow", 0.55), x, y, r * 1.7)
    w = r * 0.24
    for i in range(3):
        a = math.pi / 2 + i * math.pi / 3
        poly(c, emit("snow", 1.0), capsule_pts(x, y, 2 * r, w, a), 0.01 * (i + 1), depth=0.01, name="flake")


def bolt(c, x, y, s):
    pts = [(0.06, 0.32), (-0.2, -0.04), (-0.02, -0.04), (-0.14, -0.42), (0.22, 0.06), (0.04, 0.06), (0.16, 0.32)]
    halo(c, glow("bolt_glow", 0.8), x, y, 0.48 * s)
    poly(c, emit_ramp("bolt", ["bolt_bot", "bolt_top"], 0.37 * s), [(x + px * s, y + py * s) for px, py in pts],
         0.1, name="bolt")


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

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
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"

    # The sky is never seen (the background is transparent) but the chrome
    # clouds reflect it: pale lavender straight up, then pink on one side
    # and cyan on the other near the horizon.
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    side = nt.nodes.new("ShaderNodeMapRange")
    side.inputs["From Min"].default_value = -0.7
    side.inputs["From Max"].default_value = 0.7
    side_ramp = nt.nodes.new("ShaderNodeValToRGB")
    side_ramp.color_ramp.elements[0].color = srgb(C["sky_cyan"])
    side_ramp.color_ramp.elements[1].color = srgb(C["sky_pink"])
    nt.links.new(sep.outputs["X"], side.inputs["Value"])
    nt.links.new(side.outputs["Result"], side_ramp.inputs["Fac"])
    up = nt.nodes.new("ShaderNodeValToRGB")
    e = up.color_ramp.elements
    e[0].position, e[0].color = 0.0, srgb(C["sky_down"])
    e[1].position, e[1].color = 0.55, srgb(C["sky_mid"])
    e.new(1.0).color = srgb(C["sky_up"])
    upr = nt.nodes.new("ShaderNodeMapRange")
    upr.inputs["From Min"].default_value = -1.0
    upr.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], upr.inputs["Value"])
    nt.links.new(upr.outputs["Result"], up.inputs["Fac"])
    # Horizon band: how close the direction is to level.
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], ab.inputs[0])
    band = nt.nodes.new("ShaderNodeMapRange")
    band.inputs["From Min"].default_value = 0.0
    band.inputs["From Max"].default_value = 0.45
    band.inputs["To Min"].default_value = 1.0
    band.inputs["To Max"].default_value = 0.0
    nt.links.new(ab.outputs[0], band.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(band.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(up.outputs["Color"], mix.inputs["A"])
    nt.links.new(side_ramp.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world

    base = coll("base")
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.25
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0, 0, 5)
    base.objects.link(cam)
    scene.camera = cam

    # Colored side lights for the chrome: cyan from the left, pink from the
    # right, a soft white from above.
    for name, key, loc, energy, size in (("light_cyan", "sky_cyan", (-3, 0.6, 1.6), 260, 2.5),
                                         ("light_pink", "sky_pink", (3, -0.6, 1.6), 260, 2.5),
                                         ("light_top", "sky_up", (-0.6, 1.0, 4), 120, 3.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.shape = "DISK"
        ld.energy = energy
        ld.size = size
        ld.color = srgb(C[key])[:3]
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        d = -lo.location
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        base.objects.link(lo)

    sun(coll("sun"), 0, 0, 0.68)
    sun(coll("sun_small"), -0.3, 0.3, 0.46)
    moon(coll("moon"), 0.04, 0.02, 0.68)
    moon(coll("moon_small"), -0.3, 0.3, 0.46)
    st = coll("stars")
    for x, y, r, g in ((0.66, 0.6, 0.13, "star_glow"), (0.78, 0.12, 0.08, "star_glow2"),
                       (0.36, 0.86, 0.07, "star_glow2"), (-0.66, -0.64, 0.1, "star_glow")):
        sparkle(st, x, y, r, g)
    cloud(coll("cloud_small"), "cloud", 0.22, -0.2, 0.95)
    cloud(coll("cloud_big"), "cloud", 0, 0.02, 1.3)
    cloud(coll("cloud_top"), "cloud", 0, 0.25, 1.2)
    cloud(coll("cloud_dark_top"), "dark", 0, 0.25, 1.2, rough=0.22)

    tilt = math.radians(70)  # neon streaks lean a little
    rn = coll("rain")
    for x, y in ((-0.42, -0.5), (-0.05, -0.62), (0.32, -0.5), (0.14, -0.9), (-0.26, -0.88)):
        streak(rn, "rain", x, y, 0.3, 0.065, tilt)
    dz = coll("drizzle")
    for x, y in ((-0.4, -0.52), (-0.1, -0.68), (0.22, -0.55), (0.42, -0.78), (0.02, -0.94), (-0.3, -0.88)):
        streak(dz, "rain", x, y, 0.12, 0.065, tilt)
    sn = coll("snow")
    for x, y, r in ((-0.4, -0.55, 0.13), (0.05, -0.7, 0.15), (0.42, -0.55, 0.12), (-0.18, -0.95, 0.1), (0.28, -0.95, 0.1)):
        flake(sn, x, y, r)
    sl = coll("sleet")
    for x, y in ((-0.38, -0.55), (0.3, -0.62)):
        streak(sl, "rain", x, y, 0.3, 0.065, tilt)
    for x, y, r in ((-0.02, -0.78, 0.12), (-0.36, -0.98, 0.09), (0.36, -0.98, 0.09)):
        flake(sl, x, y, r)
    fg = coll("fog")
    for i, (x, y, w) in enumerate(((-0.1, 0.48, 1.6), (0.12, 0.16, 1.9), (-0.08, -0.16, 1.8), (0.1, -0.48, 1.5))):
        key = "fog2" if i % 2 else "fog"
        poly(fg, fade_x(key, w / 2), capsule_pts(x, y, w, 0.08), 0.0, depth=0.01, name="fog")
        poly(fg, fade_x(key, w / 2 * 1.1, 0.3), capsule_pts(x, y, w * 1.1, 0.24), -0.1,
             depth=0.005, name="fog_glow")
    bolt(coll("bolt"), 0.02, -0.66, 1.3)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
build()
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(argv[0]) if argv else "retro.blend")
print("SAVED")
