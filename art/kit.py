# Shared helpers for the skin build scripts (build_<skin>.py).
#
# Most skins are flat artwork: colored shapes seen from straight above,
# with no lighting. A build script defines a Style (how to draw a sun, a
# cloud, a raindrop and so on) and calls kit.build(style). kit puts every
# element in the same place as in the other skins and in the collections
# render_skin.py expects, then saves the .blend named after the command
# line argument.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_ink.py -- art/ink.blend

import math
import sys

import bmesh
import bpy

# ---- colors and materials --------------------------------------------------


def srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


_mats = {}


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    _mats[name] = m
    return m, nt, out


def _noise(nt, scale, stretch=1.0, detail=6.0):
    # Noise texture value, spread to about 0..1. "stretch" > 1 pulls it into
    # horizontal streaks, like wood grain or a brush dragged sideways.
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / stretch, 1.0, 1.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    # Raw noise mostly sits between 0.3 and 0.7; stretch that to 0..1.
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    return mr.outputs["Result"]


def _scanlines(nt, scan, period):
    # 1 - scan .. 1, in horizontal stripes "period" world units apart, lined
    # up across every shape like the lines of a CRT screen.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = 2 * math.pi / period
    sn = nt.nodes.new("ShaderNodeMath")
    sn.operation = "SINE"
    st = nt.nodes.new("ShaderNodeMath")
    st.operation = "MULTIPLY_ADD"
    st.inputs[1].default_value = scan / 2
    st.inputs[2].default_value = 1.0 - scan / 2
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], k.inputs[0])
    nt.links.new(k.outputs[0], sn.inputs[0])
    nt.links.new(sn.outputs[0], st.inputs[0])
    return st.outputs[0]


def _finish(m, nt, out, color, alpha, alpha_fac=None, grain=0.0, grain_fac=None, scan=0.0, scan_period=0.026):
    """Wire an emission of "color" (an RGBA tuple or a color socket) to the
    output, with optional grain, scanlines and see-through."""
    em = nt.nodes.new("ShaderNodeEmission")
    col = color
    for amount, fac in ((grain, grain_fac), (scan, None)):
        if not amount:
            continue
        if fac is None:
            fac = _scanlines(nt, scan, scan_period)
        else:
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY_ADD"
            mul.inputs[1].default_value = amount
            mul.inputs[2].default_value = 1.0 - amount / 2
            nt.links.new(fac, mul.inputs[0])
            fac = mul.outputs[0]
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        if isinstance(col, tuple):
            sc.inputs[0].default_value = col[:3]
        else:
            nt.links.new(col, sc.inputs[0])
        nt.links.new(fac, sc.inputs["Scale"])
        col = sc.outputs[0]
    if isinstance(col, tuple):
        em.inputs["Color"].default_value = col
    else:
        nt.links.new(col, em.inputs["Color"])
    if alpha >= 1.0 and alpha_fac is None:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        return m
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    if alpha_fac is not None:
        nt.links.new(alpha_fac, mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def flat(color, alpha=1.0, grain=0.0, grain_scale=60.0, stretch=1.0, alpha_grain=0.0, scan=0.0):
    """Unlit color. grain: how much the brightness varies with a noise
    texture (film grain, paper, wood). alpha_grain: how much the opacity
    varies (ink and paint that soaks in unevenly). scan: how dark the gaps
    between CRT scanlines are."""
    name = f"flat_{color}_{alpha}_{grain}_{grain_scale}_{stretch}_{alpha_grain}_{scan}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    m.diffuse_color = srgb(color)
    fac = _noise(nt, grain_scale, stretch) if (grain or alpha_grain) else None
    afac = None
    if alpha_grain:
        a = nt.nodes.new("ShaderNodeMath")
        a.operation = "MULTIPLY_ADD"
        a.use_clamp = True
        a.inputs[1].default_value = alpha_grain * 2
        a.inputs[2].default_value = alpha - alpha_grain
        nt.links.new(fac, a.inputs[0])
        afac = a.outputs[0]
    return _finish(m, nt, out, srgb(color), alpha, afac, grain, fac, scan)


def gradient(colors, extent, alpha=1.0, axis="Y", scan=0.0):
    """Unlit color that runs through "colors" from -extent to +extent along
    the object's own axis (bottom to top for Y)."""
    name = f"grad_{'_'.join(colors)}_{extent}_{alpha}_{axis}_{scan}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    m.diffuse_color = srgb(colors[-1])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -extent
    mr.inputs["From Max"].default_value = extent
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    while len(els) < len(colors):
        els.new(0.5)
    for i, col in enumerate(colors):
        els[i].position = i / (len(colors) - 1)
        els[i].color = srgb(col)
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[axis], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    return _finish(m, nt, out, ramp.outputs["Color"], alpha, scan=scan)


def radial(inner, outer, alpha_in=1.0, alpha_out=1.0):
    """Unlit color that blends from the middle of a disc to its rim. Use on
    disc() shapes, whose object space runs from -r to r."""
    name = f"radial_{inner}_{outer}_{alpha_in}_{alpha_out}"
    if name in _mats:
        return _mats[name]
    m, nt, out = _new(name)
    m.diffuse_color = srgb(outer)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = srgb(inner)
    mix.inputs["B"].default_value = srgb(outer)
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    nt.links.new(ln.outputs["Value"], mix.inputs["Factor"])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(mix.outputs["Result"], em.inputs["Color"])
    if alpha_in >= 1.0 and alpha_out >= 1.0:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        return m
    a = nt.nodes.new("ShaderNodeMapRange")
    a.inputs["To Min"].default_value = alpha_in
    a.inputs["To Max"].default_value = alpha_out
    nt.links.new(ln.outputs["Value"], a.inputs["Value"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(a.outputs["Result"], mx.inputs["Fac"])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


# ---- scene -----------------------------------------------------------------


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def setup(samples=32, res=512, gpu=True, denoise=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    if gpu:
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
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    scene.cycles.max_bounces = 0 if not denoise else 8
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.world = world
    base = coll("base")
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.25
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0, 0, 5)
    base.objects.link(cam)
    scene.camera = cam
    return scene


def lit(energy=2.2, catcher=True):
    """Switch a scene from flat art to real light: a white sky, a sun from
    the top left and (optionally) a shadow catcher, so solid shapes cast
    soft shadows on the transparent background. For skins made of 3D
    objects (clay, felt)."""
    scene = bpy.context.scene
    scene.cycles.max_bounces = 6
    scene.cycles.use_denoising = True
    scene.cycles.samples = max(scene.cycles.samples, 96)
    scene.view_settings.exposure = -0.7
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    base = coll("base")
    sd = bpy.data.lights.new("light", "SUN")
    sd.energy = energy
    sd.angle = math.radians(8)
    light = bpy.data.objects.new("light", sd)
    light.rotation_euler = (math.radians(-28), math.radians(-24), 0)
    base.objects.link(light)
    if catcher:
        bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.05))
        o = bpy.context.active_object
        o.name = "shadow_catcher"
        o.is_shadow_catcher = True
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        base.objects.link(o)


def save():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(argv[0]))
    print("SAVED")


# ---- shapes ----------------------------------------------------------------
# Every shape is a thin slab at height z. Higher z covers lower z. Shapes
# that overlap must not share a height, or Cycles shades the overlap black,
# so put() nudges each new shape up a hair.

_lift = [0.0]


def put(o, m, c):
    _lift[0] += 0.0002
    o.location.z += _lift[0]
    o.data.materials.append(m)
    for uc in list(o.users_collection):
        uc.objects.unlink(o)
    c.objects.link(o)
    return o


def poly(c, m, pts, z=0.0, name="shape"):
    ax = sum(p[0] for p in pts) / len(pts)
    ay = sum(p[1] for p in pts) / len(pts)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x - ax, y - ay, 0)) for x, y in pts]
    bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (ax, ay, z)
    bpy.context.scene.collection.objects.link(o)
    return put(o, m, c)


def stroke(c, m, pts, w, z=0.0, closed=True, name="line"):
    """A line of width w through the points, with round joints: line art
    instead of a filled shape."""
    ax = sum(p[0] for p in pts) / len(pts)
    ay = sum(p[1] for p in pts) / len(pts)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    segs = list(zip(pts, pts[1:] + pts[:1])) if closed else list(zip(pts, pts[1:]))
    for (x0, y0), (x1, y1) in segs:
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        if d < 1e-9:
            continue
        nx, ny = -dy / d * w / 2, dx / d * w / 2
        vs = [bm.verts.new((px - ax, py - ay, 0)) for px, py in
              ((x0 + nx, y0 + ny), (x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny))]
        bm.faces.new(vs)
    # Round caps at open ends, and round joints where the line turns (smooth
    # curves skip them to stay light).
    for i, (px, py) in enumerate(pts):
        end = not closed and i in (0, len(pts) - 1)
        if not end:
            prev, nxt = pts[i - 1], pts[(i + 1) % len(pts)]
            a1 = math.atan2(py - prev[1], px - prev[0])
            a2 = math.atan2(nxt[1] - py, nxt[0] - px)
            if abs(math.remainder(a2 - a1, 2 * math.pi)) < 0.2:
                continue
        vs = [bm.verts.new((px - ax + w / 2 * math.cos(2 * math.pi * k / 16),
                            py - ay + w / 2 * math.sin(2 * math.pi * k / 16), 0)) for k in range(16)]
        bm.faces.new(vs)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (ax, ay, z)
    bpy.context.scene.collection.objects.link(o)
    return put(o, m, c)


def dashed(c, m, pts, w, dash, gap, z=0.0, closed=True, name="dash"):
    """A dashed line through the points: dashes of length "dash" with
    "gap" between them."""
    path = pts + pts[:1] if closed else pts
    pieces, cur, pos, on = [], [path[0]], 0.0, True
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while d - t > 1e-9:
            left = (dash if on else gap) - pos
            step = min(left, d - t)
            t += step
            pos += step
            p = (x0 + (x1 - x0) * t / d, y0 + (y1 - y0) * t / d)
            if on:
                cur.append(p)
            if pos >= (dash if on else gap) - 1e-9:
                if on and len(cur) > 1:
                    pieces.append(cur)
                on, pos, cur = not on, 0.0, [p]
    if on and len(cur) > 1:
        pieces.append(cur)
    for piece in pieces:
        stroke(c, m, piece, w, z, False, name)


def sector_pts(x, y, r, a0, a1, steps=48):
    """A slice of a circle from angle a0 to a1 (radians), point at (x, y).
    a1 - a0 = pi gives a half circle."""
    return [(x, y)] + [(x + r * math.cos(a0 + (a1 - a0) * i / steps), y + r * math.sin(a0 + (a1 - a0) * i / steps))
                       for i in range(steps + 1)]


def wobble(pts, amp=0.008, seed=0.0):
    """Nudge each point a little, smoothly, so lines look hand drawn."""
    out = []
    for i, (x, y) in enumerate(pts):
        t = i * 0.35 + seed
        out.append((x + amp * math.sin(t * 1.7) + amp * 0.5 * math.sin(t * 4.1),
                    y + amp * math.cos(t * 1.3) + amp * 0.5 * math.sin(t * 3.3)))
    return out


def circle_pts(x, y, r, steps=96):
    return [(x + r * math.cos(2 * math.pi * i / steps), y + r * math.sin(2 * math.pi * i / steps)) for i in range(steps)]


def disc(c, m, x, y, r, z=0.0, name="disc", unit=False):
    """A filled circle. unit=True builds it at radius 1 and scales the
    object, so materials such as radial() see 0 in the middle and 1 at the
    rim."""
    rr = 1.0 if unit else r
    pts = [(x + rr * math.cos(2 * math.pi * i / 96), y + rr * math.sin(2 * math.pi * i / 96)) for i in range(96)]
    if unit:
        pts = [(px - x, py - y) for px, py in pts]
        o = poly(c, m, pts, z, name)
        o.location.x, o.location.y = x, y
        o.scale = (r, r, 1)
        return o
    return poly(c, m, pts, z, name)


def ring_pts(x, y, r_out, r_in, a0=0.0, a1=2 * math.pi, steps=96, taper=0.0):
    """A ring, or an arc of one. taper > 0 thins the arc toward both ends
    like a brush stroke."""
    outer, inner = [], []
    for i in range(steps + 1):
        t = i / steps
        a = a0 + (a1 - a0) * t
        w = (r_out - r_in)
        if taper:
            w *= 1 - taper * (abs(2 * t - 1) ** 2)
        mid = (r_out + r_in) / 2
        outer.append((x + (mid + w / 2) * math.cos(a), y + (mid + w / 2) * math.sin(a)))
        inner.append((x + (mid - w / 2) * math.cos(a), y + (mid - w / 2) * math.sin(a)))
    return outer + inner[::-1]


def capsule_pts(x, y, w, h, angle=0.0, taper=0.0):
    """Rounded bar centered on (x, y). taper > 0 narrows the right end, so
    the bar reads as a brush stroke."""
    r = h / 2
    rr = r * (1 - taper)
    pts = []
    for i in range(13):
        a = math.pi / 2 + math.pi * i / 12
        pts.append((-w / 2 + r + r * math.cos(a), r * math.sin(a)))
    for i in range(13):
        a = -math.pi / 2 + math.pi * i / 12
        pts.append((w / 2 - rr + rr * math.cos(a), rr * math.sin(a)))
    ca, sa = math.cos(angle), math.sin(angle)
    return [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]


def star_pts(x, y, r, points=4, inner=0.38):
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.pi / 2 + math.pi * i / points
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return pts


def drop_pts(x, y, r, tilt=0.35):
    tip = (x + r * 2.4 * math.sin(tilt), y + r * 2.4 * math.cos(tilt))
    dx, dy = tip[0] - x, tip[1] - y
    d = math.hypot(dx, dy)
    t = math.atan2(dy, dx)
    a = math.acos(r / d)
    pts = [tip]
    for i in range(25):
        ang = t + a + (2 * math.pi - 2 * a) * i / 24
        pts.append((x + r * math.cos(ang), y + r * math.sin(ang)))
    return pts


def crescent_pts(x, y, r, cut=0.82, ox=0.5, oy=0.36, steps=64):
    """A crescent moon: a circle of radius r at (x, y) with a circle of
    radius cut * r, offset by (ox, oy) * r, taken out of it."""
    r2 = cut * r
    c2x, c2y = x + ox * r, y + oy * r
    d = math.hypot(c2x - x, c2y - y)
    base = math.atan2(c2y - y, c2x - x)
    a = (r * r - r2 * r2 + d * d) / (2 * d)
    al = math.acos(max(-1.0, min(1.0, a / r)))
    pts = []
    # Outer edge: the long way round, away from the cut.
    for i in range(steps + 1):
        t = base + al + (2 * math.pi - 2 * al) * i / steps
        pts.append((x + r * math.cos(t), y + r * math.sin(t)))
    # Inner edge: along the cut circle, back to the start, through the side
    # facing the moon's middle.
    p_end, p_start = pts[-1], pts[0]
    f2 = math.atan2(p_end[1] - c2y, p_end[0] - c2x)
    f1 = math.atan2(p_start[1] - c2y, p_start[0] - c2x)
    dl = (f1 - f2) % (2 * math.pi)
    if math.cos(f2 + dl / 2 - (base + math.pi)) < 0:
        dl -= 2 * math.pi
    for i in range(1, steps):
        t = f2 + dl * i / steps
        pts.append((c2x + r2 * math.cos(t), c2y + r2 * math.sin(t)))
    return pts


def grow_pts(pts, k):
    """Scale a shape about its middle (for outlines and shadows)."""
    ax = sum(p[0] for p in pts) / len(pts)
    ay = sum(p[1] for p in pts) / len(pts)
    return [(ax + (px - ax) * k, ay + (py - ay) * k) for px, py in pts]


BOLT = [(0.06, 0.32), (-0.2, -0.04), (-0.02, -0.04), (-0.14, -0.42), (0.22, 0.06), (0.04, 0.06), (0.16, 0.32)]


def bolt_pts(x, y, s, grow=1.0):
    cx = sum(p[0] for p in BOLT) / len(BOLT)
    cy = sum(p[1] for p in BOLT) / len(BOLT)
    return [(x + (cx + (px - cx) * grow) * s, y + (cy + (py - cy) * grow) * s) for px, py in BOLT]


def flake_arms(x, y, r, w, angle=math.pi / 2):
    """Three bars crossing at (x, y): a six-armed snowflake."""
    return [capsule_pts(x, y, 2 * r, w, angle + i * math.pi / 3) for i in range(3)]


# The Bitcoin sign: a B with two short bars through the top and bottom,
# tilted a little like the logo. About 1.3 tall at k = 1.


def btc_lines(x, y, k):
    """The sign's strokes as point lists, centered on (x, y), scaled by k."""
    def arc(cx, cy, r, steps=16):
        return [(cx + r * math.cos(math.radians(90 - 180 * i / steps)), cy + r * math.sin(math.radians(90 - 180 * i / steps)))
                for i in range(steps + 1)]

    parts = [
        [(-0.34, 0.5), (0.05, 0.5)] + arc(0.05, 0.25, 0.25) + [(-0.2, 0.0)],
        [(-0.2, 0.0), (0.08, 0.0)] + arc(0.08, -0.25, 0.25) + [(-0.34, -0.5)],
        [(-0.2, 0.5), (-0.2, -0.5)],
        [(-0.1, 0.5), (-0.1, 0.66)], [(0.06, 0.5), (0.06, 0.66)],
        [(-0.1, -0.5), (-0.1, -0.66)], [(0.06, -0.5), (0.06, -0.66)],
    ]
    tilt = math.radians(-14)
    ct, st = math.cos(tilt), math.sin(tilt)
    return [[(x + ((px + 0.04) * ct - py * st) * k, y + ((px + 0.04) * st + py * ct) * k) for px, py in pts]
            for pts in parts]


def btc(c, m, x, y, k, w, z=0.0, name="btc"):
    """Draw the Bitcoin sign with lines of width w. Returns its objects."""
    return [stroke(c, m, pts, w, z, False, name) for pts in btc_lines(x, y, k)]


# Cloud outline as round puffs on a flat rounded base, same as Paper cut.
PUFFS = [(-0.47, -0.08, 0.3), (-0.12, 0.14, 0.4), (0.3, 0.02, 0.33), (0.02, -0.12, 0.3)]


def cloud_shapes(x, y, s, grow=1.0, dx=0.0, dy=0.0):
    """The circles and base bar that make a cloud: (circles, base points).
    grow > 1 makes a slightly bigger copy for an outline or shadow."""
    circles = [(x + (cx + dx) * s, y + (cy + dy) * s, r * s * grow) for cx, cy, r in PUFFS]
    base = capsule_pts(x + dx * s, y + (-0.2 + dy) * s, 1.32 * s * grow, 0.36 * s * grow)
    return circles, base


def cloud_outline(x, y, s, grow=1.0, dx=0.0, dy=0.0):
    """The cloud as one outline, so a see-through cloud has no visible
    overlaps between its puffs."""
    circles, _ = cloud_shapes(x, y, s, grow, dx, dy)
    bx, by = x + dx * s, y + (-0.2 + dy) * s
    bw, bh = 1.32 * s * grow, 0.36 * s * grow
    br = bh / 2
    seg = (bx - bw / 2 + br, bx + bw / 2 - br)  # base bar as a fat line

    def inside(px, py):
        for cx, cy, r in circles:
            if (px - cx) ** 2 + (py - cy) ** 2 < (r - 1e-6) ** 2:
                return True
        qx = min(max(px, seg[0]), seg[1])
        return (px - qx) ** 2 + (py - by) ** 2 < (br - 1e-6) ** 2

    edge = []
    for cx, cy, r in circles + [(seg[0], by, br), (seg[1], by, br)]:
        for i in range(240):
            a = 2 * math.pi * i / 240
            edge.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(121):
        px = seg[0] + (seg[1] - seg[0]) * i / 120
        edge += [(px, by - br), (px, by + br)]
    edge = [p for p in edge if not inside(*p)]
    # The cloud is round enough that sorting the edge by angle around its
    # middle walks the outline in order.
    mx, my = x + dx * s, y + (-0.05 + dy) * s
    edge.sort(key=lambda p: math.atan2(p[1] - my, p[0] - mx))
    out = []
    for p in edge:  # drop points too close together
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 0.004:
            out.append(p)
    return out


def cloud_flat(c, m, x, y, s, z=0.0, grow=1.0, dx=0.0, dy=0.0):
    return poly(c, m, cloud_outline(x, y, s, grow, dx, dy), z, "cloud")


# ---- the shared layout -------------------------------------------------------
# Where each element sits, matching the Paper cut, 8-bit and Retro-future
# skins: a big centered sun or moon, a small one top-left behind a cloud,
# and precipitation falling below a cloud near the top.

L = {
    "sun": (0, 0, 1.15), "sun_small": (-0.33, 0.33, 0.78),
    "moon": (0.05, 0.02, 1.15), "moon_small": (-0.3, 0.32, 0.8),
    "stars": [(0.6, 0.55, 0.11), (0.72, 0.12, 0.07), (0.38, 0.78, 0.06), (-0.62, -0.6, 0.08)],
    "cloud_small": (0.22, -0.2, 0.95), "cloud_big": (0, 0.02, 1.3), "cloud_top": (0, 0.25, 1.2),
    "rain": [(-0.42, -0.5), (-0.05, -0.68), (0.32, -0.5), (0.12, -0.92), (-0.28, -0.88)],
    "drizzle": [(-0.4, -0.52), (-0.1, -0.7), (0.22, -0.55), (0.42, -0.78), (0.0, -0.95), (-0.3, -0.88)],
    "snow": [(-0.4, -0.55, 0.13), (0.05, -0.7, 0.15), (0.42, -0.55, 0.12), (-0.18, -0.95, 0.1), (0.28, -0.95, 0.1)],
    "sleet_rain": [(-0.38, -0.55), (0.3, -0.62)],
    "sleet_snow": [(-0.02, -0.78, 0.12), (-0.36, -0.98, 0.09), (0.36, -0.98, 0.09)],
    "fog": [(-0.1, 0.48, 1.4), (0.12, 0.16, 1.6), (-0.08, -0.16, 1.5), (0.1, -0.48, 1.3)],
    "bolt": (0.02, -0.62, 1.0),
}


class Style:
    """Override these to draw a skin. c is the collection to draw into, z
    the height to draw at (clouds sit above suns, so a cloud covers the
    small sun behind it)."""

    def sun(self, c, x, y, s, z): ...
    def moon(self, c, x, y, s, z): ...
    def star(self, c, x, y, r, z): ...
    def cloud(self, c, x, y, s, z, dark): ...
    def raindrop(self, c, x, y, z): ...
    def drizzle(self, c, x, y, z): ...
    def flake(self, c, x, y, r, z): ...
    def fog(self, c, bars, z): ...
    def bolt(self, c, x, y, s, z): ...


def build(style):
    sun_z, cloud_z, fall_z = 0.0, 0.2, 0.1
    style.sun(coll("sun"), *L["sun"], sun_z)
    style.sun(coll("sun_small"), *L["sun_small"], sun_z)
    style.moon(coll("moon"), *L["moon"], sun_z)
    style.moon(coll("moon_small"), *L["moon_small"], sun_z)
    st = coll("stars")
    for x, y, r in L["stars"]:
        style.star(st, x, y, r, sun_z)
    style.cloud(coll("cloud_small"), *L["cloud_small"], cloud_z, False)
    style.cloud(coll("cloud_big"), *L["cloud_big"], cloud_z, False)
    style.cloud(coll("cloud_top"), *L["cloud_top"], cloud_z, False)
    style.cloud(coll("cloud_dark_top"), *L["cloud_top"], cloud_z, True)
    rn = coll("rain")
    for x, y in L["rain"]:
        style.raindrop(rn, x, y, fall_z)
    dz = coll("drizzle")
    for x, y in L["drizzle"]:
        style.drizzle(dz, x, y, fall_z)
    sn = coll("snow")
    for x, y, r in L["snow"]:
        style.flake(sn, x, y, r, fall_z)
    sl = coll("sleet")
    for x, y in L["sleet_rain"]:
        style.raindrop(sl, x, y, fall_z)
    for x, y, r in L["sleet_snow"]:
        style.flake(sl, x, y, r, fall_z)
    style.fog(coll("fog"), L["fog"], sun_z)
    style.bolt(coll("bolt"), *L["bolt"], fall_z)


class Plain(Style):
    """Simple friendly weather symbols drawn smaller and moved, for skins
    that show the weather inside something (a jar, a die, a dial). k is the
    scale and (ox, oy) the shift. outline, if given, is a color drawn as an
    even border around every shape, ow its width."""

    def __init__(self, k, oy=0.0, ox=0.0, outline=None, ow=0.02):
        self.k, self.ox, self.oy, self.outline, self.ow = k, ox, oy, outline, ow

    def t(self, x, y, s=1.0):
        return x * self.k + self.ox, y * self.k + self.oy, s * self.k

    def fill(self, c, color, pts, z, name, alpha=1.0):
        if self.outline:
            stroke(c, flat(self.outline), pts, 2 * self.ow, z, True, "outline")
        return poly(c, flat(color, alpha), pts, z, name)

    def sun(self, c, x, y, s, z):
        x, y, s = self.t(x, y, s)
        for i in range(10):
            a = 2 * math.pi * i / 10
            self.fill(c, "#F5A93B", capsule_pts(x + 0.68 * s * math.cos(a), y + 0.68 * s * math.sin(a), 0.22 * s, 0.1 * s, a),
                      z, "ray")
        if self.outline:
            self.fill(c, "#F9C74F", circle_pts(x, y, 0.48 * s), z, "sun")
        else:
            disc(c, flat("#F9C74F"), x, y, 0.48 * s, z, "sun")

    def moon(self, c, x, y, s, z):
        x, y, s = self.t(x, y, s)
        self.fill(c, "#E9C55A", crescent_pts(x, y, 0.55 * s), z, "moon")

    def star(self, c, x, y, r, z):
        x, y, r = self.t(x, y, r)
        self.fill(c, "#F9C74F", star_pts(x, y, r * 1.5, 4, 0.3), z, "star")

    def cloud(self, c, x, y, s, z, dark):
        x, y, s = self.t(x, y, s)
        low, top = ("#6F7C8C", "#8E9BAB") if dark else ("#C9D6E0", "#FFFFFF")
        self.fill(c, low, cloud_outline(x, y, s), z, "cloud")
        poly(c, flat(top), cloud_outline(x, y + 0.04 * s, s, 0.9), z, "cloud")

    def raindrop(self, c, x, y, z):
        x, y, _ = self.t(x, y)
        self.fill(c, "#4A90D9", drop_pts(x, y, 0.105 * self.k, 0.25), z, "drop")

    def drizzle(self, c, x, y, z):
        x, y, _ = self.t(x, y)
        if self.outline:
            self.fill(c, "#4A90D9", circle_pts(x, y, 0.058 * self.k, 32), z, "drop")
        else:
            disc(c, flat("#4A90D9"), x, y, 0.058 * self.k, z, "drop")

    def flake(self, c, x, y, r, z):
        x, y, r = self.t(x, y, r)
        k = self.k
        for arm in flake_arms(x, y, r * 1.2 + 0.023 * k, 0.106 * k):
            self.fill(c, "#8FB3CC", arm, z, "edge")
        for arm in flake_arms(x, y, r * 1.2, 0.058 * k):
            poly(c, flat("#FFFFFF"), arm, z, "flake")

    def fog(self, c, bars, z):
        for x, y, w in bars:
            x, y, w = self.t(x, y, w)
            self.fill(c, "#9FB4C4", capsule_pts(x, y, w, 0.19 * self.k), z, "fog", 0.85)

    def bolt(self, c, x, y, s, z):
        x, y, s = self.t(x, y, s)
        self.fill(c, "#F9C74F", bolt_pts(x, y, s, 1.2), z, "bolt")
