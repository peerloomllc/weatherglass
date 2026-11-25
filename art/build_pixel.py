# Build the starter "8-bit" skin scene and save it as art/pixel.blend.
#
#   flatpak run org.blender.Blender -b --factory-startup -P art/build_pixel.py -- art/pixel.blend
#
# Real pixel art: the camera sees a 36 x 36 grid and every filled cell is one
# flat square of a single color, rendered without lighting or smoothing.
# Rendered at 360 x 360, each cell is exactly 10 x 10 pixels, so the pictures
# stay sharp. install_skin.sh copies this skin without resizing.
#
# Sprites are drawn here with simple shapes (pixel circles, bars), then given
# a dark outline, a light top-left edge and a shaded bottom-right edge. In
# Blender each color of each element is one mesh of squares, so cells can be
# added, deleted or recolored by hand. Keep the collection names, since
# render_skin.py uses them to pick what each weather picture shows.

import sys

import bmesh
import bpy

N = 36  # cells across the picture
CELL = 2.25 / N  # world size of one cell (camera covers -1.125..1.125)

# 8-bit palette, picked to sit on the skin's navy background (#1C1F4A).
C = {
    "ink": "#0B0D26",  # outline
    "sun": "#FFCC33", "sun_hi": "#FFF08A", "sun_lo": "#F08A24", "ray": "#F08A24",
    "moon": "#F4F4F4", "moon_hi": "#FFFFFF", "moon_lo": "#B9BEE6", "crater": "#A3A8D9",
    "star": "#FFCC33", "star_hi": "#FFF08A",
    "cloud": "#F4F4F4", "cloud_hi": "#FFFFFF", "cloud_lo": "#B9BEE6",
    "dark": "#7A80B8", "dark_hi": "#A3A8D9", "dark_lo": "#4E5390",
    "rain": "#4FC3F7", "rain_hi": "#C8F0FF",
    "snow": "#FFFFFF", "snow_lo": "#A8D8F0",
    "fog": "#A3A8D9", "fog2": "#7A80B8",
    "bolt": "#FFE14D", "bolt_lo": "#F08A24",
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
    m = bpy.data.materials.new("px_" + key)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = srgb(C[key])
    em.inputs["Strength"].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    m.diffuse_color = srgb(C[key])  # so the viewport shows the color too
    _mats[key] = m
    return m


# ---- drawing on a grid --------------------------------------------------
# A sprite is a dict {(x, y): color key}, x to the right, y up, 0..N-1.


def circle(cx, cy, r):
    return {(x, y) for x in range(N) for y in range(N)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def rect(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def shade(cells, body, hi, lo):
    # Light on the top-left edge, shadow on the bottom-right edge.
    out = {}
    for x, y in cells:
        if (x - 1, y + 1) not in cells or (x, y + 1) not in cells:
            out[(x, y)] = hi
        elif (x + 1, y - 1) not in cells or (x, y - 1) not in cells:
            out[(x, y)] = lo
        else:
            out[(x, y)] = body
    return out


def outline(cells):
    ring = set()
    for x, y in cells:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in cells and 0 <= p[0] < N and 0 <= p[1] < N:
                ring.add(p)
    return {p: "ink" for p in ring}


def sprite(cells, body, hi, lo):
    s = outline(cells)
    s.update(shade(cells, body, hi, lo))
    return s


def paint(dst, src):
    dst.update(src)
    return dst


def sun(cx, cy, r):
    s = {}
    rays = set()
    gap, long = 2, max(3, round(r * 0.45))
    for i in range(long):
        d = r + gap + i
        for w in (-1, 0):
            rays |= {(cx + w, cy + d), (cx + w, cy - d - 1), (cx + d, cy + w), (cx - d - 1, cy + w)}
    for i in range(max(2, long - 1)):
        d = round((r + gap) * 0.72) + i
        rays |= {(cx + d, cy + d), (cx - d - 1, cy + d), (cx + d, cy - d - 1), (cx - d - 1, cy - d - 1)}
    rays = {(x, y) for x, y in rays if 0 <= x < N and 0 <= y < N}
    paint(s, outline(rays))
    paint(s, {p: "ray" for p in rays})
    body = circle(cx, cy, r)
    paint(s, sprite(body, "sun", "sun_hi", "sun_lo"))
    return s


def moon(cx, cy, r):
    body = circle(cx, cy, r) - circle(cx + r * 0.55, cy + r * 0.4, r * 0.85)
    s = sprite(body, "moon", "moon_hi", "moon_lo")
    for x, y, cr in ((-0.45, -0.1, 1.2), (-0.15, -0.6, 0.9)):
        for p in circle(cx + x * r, cy + y * r, cr):
            if p in body and s.get(p) == "moon":
                s[p] = "crater"
    return s


def star(cx, cy, big):
    if big:
        cells = {(cx, cy), (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1),
                 (cx + 2, cy), (cx - 2, cy), (cx, cy + 2), (cx, cy - 2)}
    else:
        cells = {(cx, cy), (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)}
    s = outline(cells)
    s.update({p: "star" for p in cells})
    s[(cx, cy)] = "star_hi"
    return s


def cloud(cx, cy, k, dark=False):
    # cx, cy: middle of the cloud's flat bottom; k: size.
    cells = (circle(cx - 6 * k, cy + 3.2 * k, 3.6 * k) | circle(cx, cy + 5 * k, 5.2 * k)
             | circle(cx + 6 * k, cy + 3.4 * k, 3.4 * k)
             | rect(round(cx - 8.5 * k), round(cy), round(cx + 8.5 * k) - 1, round(cy + 3 * k)))
    cells = {(x, y) for x, y in cells if y >= round(cy)}  # flat bottom
    if dark:
        return sprite(cells, "dark", "dark_hi", "dark_lo")
    return sprite(cells, "cloud", "cloud_hi", "cloud_lo")


def drops(points, length):
    # Two cells wide, slanting one cell left every two rows.
    s = {}
    for x, y in points:
        cells = {(x - i // 2 + w, y - i) for i in range(length) for w in (0, 1)}
        paint(s, outline(cells))
        paint(s, {p: "rain" for p in cells})
        s[(x, y)] = s[(x + 1, y)] = "rain_hi"
    return s


def flakes(points):
    s = {}
    for x, y in points:
        cells = {(x + dx, y) for dx in range(-2, 3)} | {(x, y + dy) for dy in range(-2, 3)}
        cells |= {(x - 1, y - 1), (x + 1, y + 1), (x - 1, y + 1), (x + 1, y - 1)}
        paint(s, outline(cells))
        paint(s, {p: "snow" for p in cells})
        s[(x, y)] = "snow_lo"
    return s


def bolt(x0, y0):
    rows = [  # cells per row, top to bottom, as (start, end) offsets from x0
        (5, 9), (5, 8), (4, 8), (4, 7), (3, 7), (3, 6), (2, 6), (2, 10), (1, 10), (1, 9),
        (5, 9), (5, 8), (4, 8), (4, 7), (4, 6), (3, 6), (3, 5), (3, 4), (2, 3),
    ]
    cells = set()
    for i, (a, b) in enumerate(rows):
        for x in range(a, b + 1):
            cells.add((x0 + x, y0 - i))
    s = outline(cells)
    s.update(shade(cells, "bolt", "bolt", "bolt_lo"))
    return s


def fog():
    s = {}
    bars = ((6, 26, 25, 27), (9, 20, 31, 21), (4, 14, 27, 15), (10, 8, 30, 9))
    for i, (x0, y0, x1, y1) in enumerate(bars):
        cells = rect(x0, y0, x1, y1)
        paint(s, outline(cells))
        paint(s, {p: ("fog2" if i % 2 else "fog") for p in cells})
    return s


# ---- scene ---------------------------------------------------------------


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def place(name, s, z):
    # One mesh of squares per color, so each color is easy to select and edit.
    c = coll(name)
    by_color = {}
    for p, key in s.items():
        by_color.setdefault(key, []).append(p)
    for key, cells in by_color.items():
        me = bpy.data.meshes.new(f"{name}_{key}")
        bm = bmesh.new()
        for x, y in cells:
            x0 = (x - N / 2) * CELL
            y0 = (y - N / 2) * CELL
            vs = [bm.verts.new((x0, y0, 0)), bm.verts.new((x0 + CELL, y0, 0)),
                  bm.verts.new((x0 + CELL, y0 + CELL, 0)), bm.verts.new((x0, y0 + CELL, 0))]
            bm.faces.new(vs)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=CELL * 0.01)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat(key))
        o = bpy.data.objects.new(f"{name}_{key}", me)
        # Outlines sit a hair below fills so a fill always wins where two
        # elements meet.
        o.location.z = z - (0.001 if key == "ink" else 0)
        c.objects.link(o)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"  # flat colors only; the CPU is quick enough
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.cycles.filter_width = 0.01  # no smoothing between cells
    scene.cycles.max_bounces = 0
    scene.render.resolution_x = scene.render.resolution_y = N * 10
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
    cam_data.ortho_scale = N * CELL
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (0, 0, 5)
    base.objects.link(cam)
    scene.camera = cam

    # Same layout as the Paper cut skin: precipitation falls below a cloud
    # near the top.
    place("sun", sun(18, 18, 9), 0)
    place("sun_small", sun(13, 23, 6), 0)
    place("moon", moon(18, 18, 11), 0)
    place("moon_small", moon(13, 23, 7.5), 0)
    st = {}
    for x, y, big in ((29, 29, True), (31, 18, False), (24, 33, False), (6, 7, True), (7, 30, False)):
        paint(st, star(x, y, big))
    place("stars", st, 0)

    place("cloud_small", cloud(21, 9, 0.95), 0.1)
    place("cloud_big", cloud(18, 11, 1.4), 0.1)
    place("cloud_top", cloud(18, 17, 1.3), 0.1)
    place("cloud_dark_top", cloud(18, 17, 1.3, dark=True), 0.1)

    place("rain", drops(((10, 13), (17, 11), (24, 13), (30, 10), (13, 6), (20, 4), (27, 5)), 4), 0)
    place("drizzle", drops(((10, 12), (17, 9), (24, 12), (13, 5), (21, 4), (28, 6)), 2), 0)
    place("snow", flakes(((10, 11), (18, 8), (26, 11), (13, 3), (23, 3))), 0)
    sl = drops(((10, 13), (23, 12), (17, 6)), 4)
    paint(sl, flakes(((17, 11), (28, 8), (10, 4), (25, 3))))
    place("sleet", sl, 0)
    place("bolt", bolt(13, 17), 0)
    place("fog", fog(), 0)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
build()
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath(argv[0]) if argv else "pixel.blend")
print("SAVED")
