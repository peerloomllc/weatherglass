# Render one skin's 18 weather pictures from its .blend file.
#
#   flatpak run org.blender.Blender -b art/paper.blend -P art/render_skin.py -- art/out/paper
#
# The .blend must have one collection per weather element, named exactly as
# in PARTS below. For each weather type and time of day this script shows
# only the collections that picture needs, hides the rest and renders a
# transparent PNG named <weather>_<day|night>.png into the output folder.
# Anything in other collections (camera, light, shadow catcher) is always on.
#
# With --mini, the always-on "base" collection and any object named
# "pointer..." are hidden too. Skins that draw the weather inside something
# (a jar, a die, a dial, a town) use this for a second set of pictures with
# just the weather, which the app shows at small sizes:
#
#   flatpak run org.blender.Blender -b art/dice.blend -P art/render_skin.py -- art/out/dice_mini --mini

import os
import sys

import bpy

# weather -> (day collections, night collections)
PARTS = {
    "clear": (["sun"], ["moon", "stars"]),
    "partly": (["sun_small", "cloud_small"], ["moon_small", "cloud_small"]),
    "cloudy": (["cloud_big"], ["cloud_big"]),
    "fog": (["fog"], ["fog"]),
    "drizzle": (["cloud_top", "drizzle"], ["cloud_top", "drizzle"]),
    "rain": (["cloud_dark_top", "rain"], ["cloud_dark_top", "rain"]),
    "sleet": (["cloud_dark_top", "sleet"], ["cloud_dark_top", "sleet"]),
    "snow": (["cloud_top", "snow"], ["cloud_top", "snow"]),
    "thunder": (["cloud_dark_top", "bolt"], ["cloud_dark_top", "bolt"]),
}
ALL = sorted({c for d, n in PARTS.values() for c in d + n})


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mini = "--mini" in argv
    argv = [a for a in argv if a != "--mini"]
    out = os.path.abspath(argv[0] if argv else "out")
    only = argv[1] if len(argv) > 1 else None  # e.g. "rain_day" to render one
    os.makedirs(out, exist_ok=True)

    cols = bpy.data.collections
    if mini:
        if "base" in cols:
            for o in cols["base"].objects:
                if o.type not in ("CAMERA", "EMPTY"):
                    o.hide_render = True
        for o in bpy.data.objects:
            if o.name.startswith("pointer"):
                o.hide_render = True
    missing = [c for c in ALL if c not in cols]
    if missing:
        print("WARNING: no collection for", ", ".join(missing), "- those pictures will be missing parts")

    for weather, (day, night) in PARTS.items():
        for when, shown in (("day", day), ("night", night)):
            name = f"{weather}_{when}"
            if only and name != only:
                continue
            for c in ALL:
                if c in cols:
                    cols[c].hide_render = c not in shown
            bpy.context.scene.render.filepath = os.path.join(out, name + ".png")
            bpy.ops.render.render(write_still=True)
            print("RENDERED", name)


main()
