# Render a skin's opening clips: for each of the 18 weather pictures, a short
# animation (18 frames at 12 fps, 1.5 seconds) that ends exactly on the still
# picture. The app plays it once when it opens, in place of the plain motion.
#
#   flatpak run org.blender.Blender -b art/dice.blend -P art/animate_clip.py -- art/out/dice_clip dice
#   ... -- <out folder> <style> [rain_day]      (one picture only)
#
# Styles:
#   smooth  everything eases into place (used by Retro-future, with its
#           neon glows pulsing as they come in)
#   clay    the same moves, but held two frames at a time and with a squash
#           as each piece lands, like stop-motion
#   dice    the die rolls in from the left, its numbers flicking past as it
#           tumbles, and lands on 1 for rain and thunderstorms, 20 for clear
#           skies and 10 for anything else. The number shrinks away and the
#           weather pops up on its face
#
# Every element collection is moved as one piece by an empty placed at its
# middle. The last frame has every empty back at rest, so it matches the
# still picture. Writes PNG frames to <out folder>/<picture>/f_0001.png ...;
# install_clip.sh turns them into animated WebP for the app.

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_skin import ALL, PARTS  # noqa: E402

FRAMES = 18
DICE_FRAMES = 28  # the dice clip runs longer so the rolled number can be read

# What each element does on its way in.
ROLE = {
    "sun": "rise_turn", "sun_small": "rise_turn", "moon": "rise", "moon_small": "rise", "stars": "pop",
    "cloud_small": "slide", "cloud_big": "slide", "cloud_top": "slide", "cloud_dark_top": "slide",
    "rain": "fall", "drizzle": "fall", "snow": "fall", "sleet": "fall", "fog": "slide_right", "bolt": "strike",
}


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def span(f, a, b):
    """0 before frame a, 1 after frame b, eased in between."""
    return ease((f - a) / (b - a))


def overshoot(f, a, b, peak=1.2):
    """Scale that grows from 0 past full size and settles back to 1."""
    if f <= a:
        return 0.0
    if f >= b:
        return 1.0
    t = (f - a) / (b - a)
    return min(1.0, t * 2) * peak if t < 0.5 else peak + (1 - peak) * ease((t - 0.5) * 2)


def pose(role, f, style):
    """(dx, dy, rot_z, sx, sy) for an element at frame f; all zero/one at rest."""
    dx = dy = rot = 0.0
    sx = sy = 1.0
    if style == "dice":
        # The weather pops up once the rolled number has shrunk away.
        s = overshoot(f, SHRINK_END, DICE_FRAMES, 1.25)
        return 0.0, 0.0, 0.0, s, s
    if role in ("slide", "slide_right"):
        k = 1 - span(f, 1, 11)
        dx = (-0.75 if role == "slide" else 0.75) * k
    elif role in ("rise", "rise_turn"):
        k = 1 - span(f, 1, 11)
        dy = -0.5 * k
        sx = sy = 1 - 0.35 * k
        if role == "rise_turn":
            rot = math.radians(-60) * k
    elif role == "pop":
        sx = sy = overshoot(f, 6, 14)
    elif role == "fall":
        k = 1 - span(f, 5, 15)
        dy = 0.45 * k
        sx = sy = 0.0 if f < 5 else 1.0
    elif role == "strike":
        sx = sy = overshoot(f, 9, 14, 1.35)
    if style == "clay" and role not in ("pop", "strike") and 9 <= f <= 14 and sx > 0:
        # Squash as it lands, then spring back.
        q = math.sin(math.pi * (f - 9) / 5) * 0.12
        sx, sy = sx * (1 + q), sy * (1 - q)
    return dx, dy, rot, sx, sy


def holder(coll):
    """An empty at the middle of a collection that carries all its objects."""
    objs = [o for o in coll.objects if o.type not in ("CAMERA", "LIGHT") and o.parent is None
            and o.name != "shadow_catcher"]
    if not objs:
        return None
    mid = sum((o.matrix_world.translation for o in objs), Vector()) / len(objs)
    e = bpy.data.objects.new("anim_" + coll.name, None)
    e.location = mid
    coll.objects.link(e)
    bpy.context.view_layer.update()
    inv = e.matrix_world.inverted()
    for o in objs:
        o.parent = e
        o.matrix_parent_inverse = inv
    return e


def key_all(e, poses):
    # A key on every frame, so how Blender blends between keys never matters.
    base_loc = e.location.copy()
    for f, (dx, dy, rot, sx, sy) in poses:
        e.location = base_loc + Vector((dx, dy, 0))
        e.rotation_euler = (0, 0, rot)
        e.scale = (max(sx, 1e-4), max(sy, 1e-4), 1)
        for path in ("location", "rotation_euler", "scale"):
            e.keyframe_insert(path, frame=f)
    e.location = base_loc


def dice_roll(e):
    """The die slides in from the left, spinning, and bumps to a stop."""
    base = e.location.copy()
    for f in range(1, DICE_FRAMES + 1):
        k = 1 - span(f, 1, 12)
        e.location = base + Vector((-1.4 * k, 0.15 * math.sin(math.pi * k), 0))
        e.rotation_euler = (0, 0, math.radians(600) * k)
        bump = 1 + 0.06 * math.sin(math.pi * min(1, max(0, (f - 11) / 4))) if f >= 11 else 1
        e.scale = (bump, bump, 1)
        for path in ("location", "rotation_euler", "scale"):
            e.keyframe_insert(path, frame=f)
    e.location = base


# Dice: which number the die lands on for each weather.
ROLL = {"rain": 1, "thunder": 1, "clear": 20}
ROLL_LAND = 11  # frame the die stops on
SHRINK = 19  # the number holds until here (about two thirds of a second)...
SHRINK_END = 22  # ...then shrinks away by here
FLICK = [7, 14, 3, 18, 9, 12, 5, 16, 2, 11]  # numbers shown while it tumbles
FACETS = [(13, 0.0, 0.62), (6, -0.54, -0.31), (17, 0.54, -0.31), (4, 0.0, -0.8), (19, -0.7, 0.4), (8, 0.7, 0.4)]


def number(coll, text, x, y, size, color):
    import kit  # noqa: E402  (only needed for the dice numbers)
    cu = bpy.data.curves.new("num_" + text, "FONT")
    cu.body = text
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.size = size
    cu.offset = size * 0.035  # a little bolder
    o = bpy.data.objects.new("num_" + text, cu)
    o.location = (x, y, -0.4)
    o.data.materials.append(kit.flat(color))
    coll.objects.link(o)
    return o


def dice_numbers(base):
    """The big number on the die's middle face (one object per number, shown
    one at a time), plus small numbers on the faces around it. All of them
    shrink away after the die lands."""
    big = {n: number(base, str(n), 0, -0.03, 0.42, "#F6EDD8") for n in set(FLICK + [1, 10, 20])}
    small = [number(base, str(n), x, y, 0.15, "#F2C7CC") for n, x, y in FACETS]
    for o in small:
        for f, k in ((1, 1.0), (SHRINK, 1.0), (SHRINK_END, 0.0)):
            o.scale = (k, k, 1)
            o.keyframe_insert("scale", frame=f)
    return big


def show_roll(big, target):
    """Key which big number shows on each frame for one picture."""
    for o in big.values():
        o.animation_data_clear()
        o.scale = (1, 1, 1)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
    for i, f in enumerate(range(1, ROLL_LAND)):
        o = big[FLICK[i % len(FLICK)]]
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f)
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=f + 1)
    o = big[target]
    o.hide_render = False
    o.keyframe_insert("hide_render", frame=ROLL_LAND)
    for f, k in ((ROLL_LAND, 1.2), (ROLL_LAND + 1, 1.0), (SHRINK, 1.0), (SHRINK_END, 0.0)):
        o.scale = (k, k, 1)
        o.keyframe_insert("scale", frame=f)
    o.hide_render = True
    o.keyframe_insert("hide_render", frame=SHRINK_END + 1)


def pulse_glows():
    """Retro-future: neon dims in, flares, then settles to its normal brightness."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                rest = n.inputs["Strength"].default_value
                for f, k in ((1, 0.15), (8, 1.9), (13, 1.2), (FRAMES, 1.0)):
                    n.inputs["Strength"].default_value = rest * k
                    n.inputs["Strength"].keyframe_insert("default_value", frame=f)
                n.inputs["Strength"].default_value = rest


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, style = os.path.abspath(argv[0]), argv[1]
    only = argv[2] if len(argv) > 2 else None
    scene = bpy.context.scene
    global FRAMES
    if style == "dice":
        FRAMES = DICE_FRAMES
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.fps = 12
    step = 2 if style == "clay" else 1
    cols = bpy.data.collections

    for name in ALL:
        if name not in cols:
            continue
        e = holder(cols[name])
        if e is None:
            continue
        poses = []
        for f in range(1, FRAMES + 1):
            src = f if step == 1 else min(FRAMES, f - (f - 1) % step)  # hold every other frame
            poses.append((f, pose(ROLE.get(name, "rise"), src if f < FRAMES else FRAMES, style)))
        key_all(e, poses)
    big = None
    if style == "dice" and "base" in cols:
        big = dice_numbers(cols["base"])
        e = holder(cols["base"])
        if e:
            dice_roll(e)
    if style == "smooth":
        pulse_glows()

    for weather, (day, night) in PARTS.items():
        for when, shown in (("day", day), ("night", night)):
            pic = f"{weather}_{when}"
            if only and pic != only:
                continue
            if when == "night" and night == day:
                continue  # looks the same as the day clip, which the app falls back to
            for c in ALL:
                if c in cols:
                    cols[c].hide_render = c not in shown
            if big:
                show_roll(big, ROLL.get(weather, 10))
            os.makedirs(os.path.join(out, pic), exist_ok=True)
            scene.render.filepath = os.path.join(out, pic, "f_")
            bpy.ops.render.render(animation=True)
            print("CLIP", pic)


main()
