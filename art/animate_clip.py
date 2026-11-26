# Render a skin's opening clips: for each of the 18 weather pictures, a short
# animation (18 frames at 12 fps, 1.5 seconds) that ends exactly on the still
# picture. The app plays it once when it opens, in place of the plain motion.
#
#   flatpak run org.blender.Blender -b art/dice.blend -P art/animate_clip.py -- art/out/dice_clip dice
#   ... -- <out folder> <style> [rain_day]      (one picture only)
#
# Styles:
#   smooth  everything eases into place: clouds slide in, the sun rises and
#           turns, stars and lightning pop, rain falls into place
#   glow    smooth, with every glow and shine flaring as it comes in
#           (Retro-future, Art Deco, Lo-fi)
#   steps   the smooth moves in chunky held steps, like an old game
#   popup   each piece folds up like a pop-up book page (Paper cut)
#   crt     the picture opens out of a bright line, like an old monitor
#           switching on
#   glitch  pieces jitter sideways and snap into line (Vaporwave, Risograph)
#   blink   everything blinks on like LCD segments
#   stagger pieces appear one after another, as if drawn or printed
#   bloom   pieces spread out slowly from nothing, like wet paint
#   clay    the same moves, but held two frames at a time and with a squash
#           as each piece lands, like stop-motion
#   dice    the die rolls in from the left, its numbers flicking past as it
#           tumbles, and lands on 1 for rain and thunderstorms, 20 for clear
#           skies and 10 for anything else. The number shrinks away and the
#           weather pops up on its face
#   film    Kurosawa: an old projector starting up. The picture flickers up
#           from black, the frame jumps, scratches flash across it, and rain
#           comes down hard
#   gauge   Round gauge: the dial stays put and its needle swings in from the
#           far end, overshoots and settles on today's reading
#   coin    Orange coin: the coin spins on its edge with the Bitcoin sign on
#           its face, slows and stops, then the sign shrinks away and the
#           weather pops up
#   mine    Block explorer: the blocks drop in one at a time in a scattered
#           order, as if mined, until the picture is complete
#   laser   Laser eyes: everything eases in, then the eyes fire their beams
#           out with a bright flash
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
STEP = {"clay": 2, "steps": 3}  # hold each pose this many frames
# When each kind of element starts, for the styles that bring pieces in one
# after another.
ORDER = {"slide": 1, "slide_right": 1, "rise": 3, "rise_turn": 3, "pop": 6, "fall": 8, "strike": 10}
GLITCH = [0.28, -0.2, 0.32, -0.12, 0.18, -0.24, 0.1, -0.06, 0.03]
BLINK = [0, 0, 1, 0, 0, 1, 1, 0, 1]
DICE_FRAMES = 28  # the dice clip runs longer so the rolled number can be read
GAUGE_FRAMES = 24  # room for the needle to wobble before it settles
COIN_FRAMES = 24  # the spin, a moment to see the Bitcoin sign, then the weather

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


def pose(role, f, style, mid_y=0.0, seed=0):
    """(dx, dy, rot_z, sx, sy) for an element at frame f; all zero/one at rest.
    mid_y is the element's height in the picture, for styles that squash the
    whole picture about its middle; seed varies the glitch per element."""
    dx = dy = rot = 0.0
    sx = sy = 1.0
    if f >= FRAMES:
        return dx, dy, rot, sx, sy
    if style == "popup":
        a = ORDER.get(role, 3)
        return 0.0, 0.0, 0.0, 1.0, overshoot(f, a, a + 7, 1.15)
    if style == "stagger":
        a = ORDER.get(role, 3)
        s_ = overshoot(f, a, a + 5, 1.15)
        return 0.0, 0.0, 0.0, s_, s_
    if style == "bloom":
        a = {"slide": 1, "slide_right": 1, "rise": 2, "rise_turn": 2}.get(role, 5)
        s_ = span(f, a, a + 9)
        return 0.0, 0.0, 0.0, s_, s_
    if style == "blink":
        v = BLINK[f - 1] if f <= len(BLINK) else 1
        return 0.0, 0.0, 0.0, float(v), float(v)
    if style == "glitch":
        if f > len(GLITCH):
            return dx, dy, rot, sx, sy
        j = GLITCH[(f - 1 + seed) % len(GLITCH)] * (1 - f / (len(GLITCH) + 1))
        return j, 0.0, 0.0, 1 + abs(j) * 0.8, 1.0
    if style == "crt":
        # Opens from a thin line through the middle of the picture.
        sy = 0.03 if f <= 2 else 0.03 + 0.97 * span(f, 2, 8)
        sx = 0.6 + 0.4 * span(f, 1, 4)
        return 0.0, -mid_y * (1 - sy), 0.0, sx, sy
    if style in ("gauge", "mine"):
        return 0.0, 0.0, 0.0, 1.0, 1.0  # only the needle (or each block) moves
    if style == "coin":
        s = overshoot(f, COIN_SHRINK_END, COIN_FRAMES, 1.25)
        return 0.0, 0.0, 0.0, s, s
    if style == "film":
        # Everything sits still while the frame jumps, except the rain.
        if role != "fall":
            return (0.0, JUMP.get(f, 0.0), 0.0, 1.0, 1.0)
        k = 1 - span(f, 3, 15)
        return (0.0, 0.6 * k + JUMP.get(f, 0.0), 0.0, 1.0, 1.0)
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
    """An empty at the middle of a collection that carries all its objects.
    If the objects already hang off a parent outside the collection (the
    Isometric town's camera-facing "weather" empty), the new empty hangs off
    that parent too, so its moves happen in that parent's plane."""
    objs = [o for o in coll.objects if o.type not in ("CAMERA", "LIGHT") and o.name != "shadow_catcher"
            and (o.parent is None or o.parent.name not in coll.objects)]
    if not objs:
        return None
    mid = sum((o.matrix_world.translation for o in objs), Vector()) / len(objs)
    e = bpy.data.objects.new("anim_" + coll.name, None)
    coll.objects.link(e)
    par = objs[0].parent if all(o.parent == objs[0].parent for o in objs) else None
    if par is not None:
        e.parent = par
        e.matrix_world = par.matrix_world.normalized()
        bpy.context.view_layer.update()
        e.location = par.matrix_world.inverted() @ mid
    else:
        e.location = mid
    bpy.context.view_layer.update()
    for o in objs:
        world = o.matrix_world.copy()
        o.parent = e
        o.matrix_parent_inverse = e.matrix_world.inverted() @ world @ o.matrix_basis.inverted()
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


# Coin: the spin stops here, the sign holds, then shrinks away.
COIN_STOP = 13
COIN_SHRINK = 16
COIN_SHRINK_END = 18


def btc_sign(coll):
    """The Bitcoin sign on the coin's face, in strokes hung off one empty so
    it can shrink as a whole."""
    import kit  # noqa: E402
    e = bpy.data.objects.new("btc", None)
    e.location = (0, 0, -0.4)
    coll.objects.link(e)
    bpy.context.view_layer.update()
    m = kit.flat("#F7931A")
    w, z = 0.13, -0.4

    def arc(cx, cy, r, steps=16):
        return [(cx + r * math.cos(math.radians(90 - 180 * i / steps)), cy + r * math.sin(math.radians(90 - 180 * i / steps)))
                for i in range(steps + 1)]

    k = 0.95
    parts = [
        [(-0.34, 0.5), (0.05, 0.5)] + arc(0.05, 0.25, 0.25) + [(-0.2, 0.0)],
        [(-0.2, 0.0), (0.08, 0.0)] + arc(0.08, -0.25, 0.25) + [(-0.34, -0.5)],
        [(-0.2, 0.5), (-0.2, -0.5)],
        [(-0.1, 0.5), (-0.1, 0.66)], [(0.06, 0.5), (0.06, 0.66)],
        [(-0.1, -0.5), (-0.1, -0.66)], [(0.06, -0.5), (0.06, -0.66)],
    ]
    tilt = math.radians(-14)
    ct, st = math.cos(tilt), math.sin(tilt)
    for pts in parts:
        pts = [((x + 0.04) * k * ct - y * k * st, (x + 0.04) * k * st + y * k * ct) for x, y in pts]
        o = kit.stroke(coll, m, pts, w, z, False, "btc_line")
        o.parent = e
        o.matrix_parent_inverse = e.matrix_world.inverted()
    for f, sc in ((1, 1.0), (COIN_SHRINK, 1.0), (COIN_SHRINK_END, 0.0)):
        e.scale = (max(sc, 1e-4),) * 3
        e.keyframe_insert("scale", frame=f)


def coin_spin(e):
    """The coin spins on its vertical axis (squashed sideways as it turns)
    three times, slowing down, with a small hop, and lands face up."""
    for f in range(1, COIN_FRAMES + 1):
        t = span(f, 1, COIN_STOP)
        turn = 3 * 2 * math.pi * (1 - t)
        sx = max(abs(math.cos(turn)), 0.04)
        hop = 0.18 * math.sin(math.pi * min(1.0, (f - 1) / (COIN_STOP - 1)))
        e.scale = (sx, 1, 1)
        e.location.y = hop
        e.keyframe_insert("scale", frame=f)
        e.keyframe_insert("location", frame=f)
    e.location.y = 0


def mine_blocks(cols):
    """Each block pops in on its own frame, scattered, so the picture builds
    up block by block. Done by frame 15 of 18."""
    for c in cols:
        for o in c.all_objects:
            if not o.name.startswith("cell"):
                continue
            p = o.matrix_world.translation
            r = (math.sin(p.x * 91.7 + p.y * 47.3) * 43758.5453) % 1.0
            a = 2 + int(r * 10)
            for f, k in ((1, 0.0), (a, 0.0), (a + 1, 1.3), (a + 3, 1.0)):
                o.scale = (max(k, 1e-4), max(k, 1e-4), 1)
                o.keyframe_insert("scale", frame=f)


LASER_FIRE = 11  # the beams fire here...
LASER_HIT = 14  # ...and reach full length here


def laser_fire():
    """The beams shoot out of the eyes and flare, then settle."""
    for e in bpy.data.objects:
        if not e.name.startswith("laser"):
            continue
        for f, k in ((1, 0.0), (LASER_FIRE, 0.0), (LASER_FIRE + 1, 0.45), (LASER_HIT, 1.0)):
            e.scale = (max(k, 1e-4), 1, 1)
            e.keyframe_insert("scale", frame=f)
    mats = {m for o in bpy.data.objects if o.name.startswith(("beam", "eye", "glow")) for m in o.data.materials}
    for m in mats:
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                rest = n.inputs["Strength"].default_value
                for f, k in ((1, 0.6), (LASER_FIRE, 0.6), (LASER_HIT, 2.4), (LASER_HIT + 3, 1.0), (FRAMES, 1.0)):
                    n.inputs["Strength"].default_value = rest * k
                    n.inputs["Strength"].keyframe_insert("default_value", frame=f)
                n.inputs["Strength"].default_value = rest


# Film: how far the frame jumps on the first few frames, as the projector
# catches the film.
JUMP = {2: 0.06, 3: -0.04, 5: 0.03, 7: -0.02}
FLICKER = [0.0, 0.12, 0.45, 0.2, 0.75, 0.55, 1.1, 0.85, 1.05, 0.92, 1.03, 0.97]


def film_flicker():
    """The picture flickers up from black: every color's brightness is keyed
    frame by frame, ending at its normal value."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                rest = n.inputs["Strength"].default_value
                for f in range(1, FRAMES + 1):
                    k = FLICKER[f - 1] if f <= len(FLICKER) else 1.0
                    n.inputs["Strength"].default_value = rest * k
                    n.inputs["Strength"].keyframe_insert("default_value", frame=f)
                n.inputs["Strength"].default_value = rest


def film_scratches():
    """Thin pale scratches that flash on a few early frames."""
    import kit  # noqa: E402
    c = bpy.data.collections.new("film_scratches")
    bpy.context.scene.collection.children.link(c)
    for x, frames in ((-0.42, (2, 5, 8)), (0.18, (3, 4, 9)), (0.55, (6, 10))):
        o = kit.poly(c, kit.flat("#ECE8E0", 0.7), kit.capsule_pts(x, 0.0, 2.2, 0.012, 1.5708), 0.9, "scratch")
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        for f in frames:
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=f)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=f + 1)


def gauge_needles(cols):
    """Each pointer swings in from the far end of the dial, overshoots and
    settles. The pointers sit in the weather collections (one per picture)."""
    for c in cols:
        ptr = [o for o in c.objects if o.name.startswith("pointer")]
        if not ptr:
            continue
        e = bpy.data.objects.new("needle_" + c.name, None)
        e.location = (0, 0, 0)
        c.objects.link(e)
        bpy.context.view_layer.update()
        for o in ptr:
            o.parent = e
            o.matrix_parent_inverse = e.matrix_world.inverted()
        # Where the pointer rests, as an angle round the dial's middle.
        mid = sum((o.matrix_world.translation for o in ptr), Vector()) / len(ptr)
        rest = math.atan2(mid.y, mid.x)
        # Start from whichever end of the dial is further away.
        far = math.radians(165) if rest < math.radians(90) else math.radians(15)
        swing = far - rest
        for f in range(1, FRAMES + 1):
            t = (f - 1) / (FRAMES - 1)
            k = 0.0 if f == FRAMES else math.exp(-5.5 * t) * math.cos(2.4 * math.pi * t)
            e.rotation_euler = (0, 0, swing * k)
            e.keyframe_insert("rotation_euler", frame=f)


def crt_glow():
    """CRT: the line flashes bright as the tube warms, then settles."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                rest = n.inputs["Strength"].default_value
                for f, k in ((1, 0.0), (2, 2.6), (4, 1.7), (8, 1.0), (FRAMES, 1.0)):
                    n.inputs["Strength"].default_value = rest * k
                    n.inputs["Strength"].keyframe_insert("default_value", frame=f)
                n.inputs["Strength"].default_value = rest


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
    if style == "gauge":
        FRAMES = GAUGE_FRAMES
    if style == "coin":
        FRAMES = COIN_FRAMES
    scene.frame_start, scene.frame_end = 1, FRAMES
    scene.render.fps = 12
    step = STEP.get(style, 1)
    cols = bpy.data.collections

    for name in ALL:
        if name not in cols or style == "gauge":
            continue
        e = holder(cols[name])
        if e is None:
            continue
        poses = []
        for f in range(1, FRAMES + 1):
            src = f if step == 1 else min(FRAMES, f - (f - 1) % step)  # hold every other frame
            poses.append((f, pose(ROLE.get(name, "rise"), src if f < FRAMES else FRAMES, style,
                                  e.location.y, ALL.index(name))))
        key_all(e, poses)
    big = None
    if style == "coin" and "base" in cols:
        btc_sign(cols["base"])
        e = holder(cols["base"])
        if e:
            coin_spin(e)
    if style == "mine":
        mine_blocks([cols[n] for n in ALL if n in cols])
    if style == "laser":
        laser_fire()
    if style == "dice" and "base" in cols:
        big = dice_numbers(cols["base"])
        e = holder(cols["base"])
        if e:
            dice_roll(e)
    if style == "glow":
        pulse_glows()
    if style == "crt":
        crt_glow()
    if style == "film":
        film_flicker()
        film_scratches()
    if style == "gauge":
        gauge_needles([cols[n] for n in ALL if n in cols])

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
