# Skin art

Each skin can have its own picture for every weather type, made in Blender.
Pictures a skin does not have fall back to the built-in line icons. The app
ships 300px WebP pictures (see `install_skin.sh`).

## Files

| File | What it does |
| --- | --- |
| `<skin>.blend` | The skin's scene. Open it in Blender and edit by hand |
| `build_paper.py` | Builds the starter Paper cut scene from scratch (overwrites `paper.blend`) |
| `build_pixel.py` | Builds the starter 8-bit scene (overwrites `pixel.blend`) |
| `build_retro.py` | Builds the starter Retro-future scene (overwrites `retro.blend`) |
| `kit.py` | Shared drawing helpers and the common layout for flat skins |
| `build_kurosawa.py`, `build_anime.py`, `build_ukiyoe.py`, `build_ink.py`, `build_crt.py`, `build_vapor.py`, `build_lcd.py`, `build_bauhaus.py`, `build_deco.py`, `build_riso.py`, `build_blueprint.py`, `build_watercolor.py`, `build_chalk.py`, `build_barometer.py`, `build_journal.py`, `build_noir.py`, `build_lofi.py` | Flat skins built with `kit.py` |
| `build_terrarium.py`, `build_dice.py`, `build_gauge.py` | Flat skins with a jar, die or dial in the always-on `base` collection and the weather drawn smaller inside it by `kit.Plain` |
| `build_rpg.py` | 16-bit pixel art on a 48 x 48 grid, installed with hard edges |
| `build_iso.py` | Lit 3D town in `base`, with `kit.Plain` symbols turned toward an isometric camera |
| `build_clay.py`, `build_felt.py` | Lit 3D skins built with `kit.py` and `kit.lit()`. Clay takes about 2 minutes to render |
| `build_teletext.py` | Block graphics on a 24 x 24 grid, installed with hard edges like 8-bit |
| `render_skin.py` | Renders a scene into 18 transparent PNGs in `out/<skin>/` |
| `install_skin.sh` | Turns those PNGs into WebP in the app (`res/drawable-nodpi/skin_<skin>_*.webp`) |
| `render_all.sh` | Both steps: `art/render_all.sh paper` |

Rendering all 18 takes about 90 seconds on the GPU for Paper cut, about 40
for Retro-future and a few seconds for 8-bit.

## The three starter skins

- **Paper cut:** layered paper shapes with small shadows.
- **8-bit:** real pixel art on a 36 x 36 grid. Each cell is a flat square,
  one mesh per color per element, so you can add, delete or recolor cells
  in Blender. It renders at exactly 10 pixels per cell, and
  `install_skin.sh` scales it with hard edges so it stays sharp.
- **Retro-future:** neon synthwave. A striped glowing sun, chrome clouds
  that reflect a pink and cyan sky, and neon rain and lightning with a soft
  glow. Overlapping glows sit at slightly different heights, since Cycles
  shades two overlapping flat shapes at the same height black.

## How a scene is laid out

One collection per weather element. `render_skin.py` shows only the
collections each picture needs:

| Picture | Day | Night |
| --- | --- | --- |
| clear | sun | moon, stars |
| partly | sun_small, cloud_small | moon_small, cloud_small |
| cloudy | cloud_big | cloud_big |
| fog | fog | fog |
| drizzle | cloud_top, drizzle | same |
| rain | cloud_dark_top, rain | same |
| sleet | cloud_dark_top, sleet | same |
| snow | cloud_top, snow | same |
| thunder | cloud_dark_top, bolt | same |

Anything outside those collections (camera, light, shadow catcher) is in
every picture. The camera looks straight down at a square from -1.1 to 1.1.
Backgrounds stay transparent so the skin's colors show through.

## Making a new skin

The quick way for a flat skin: copy one of the short `build_<skin>.py`
scripts that use `kit.py` (`build_ink.py` is a good start), change how each
element is drawn, run it to make `<skin>.blend`, then render. Add the skin's
colors and type to `skin/Skin.kt`.

To start from a hand-made scene instead:

1. Copy `paper.blend` to `<skin>.blend` (the id from `skin/Skin.kt`, e.g.
   `pixel` or `retro`).
2. Replace the contents of each collection with your own models. Keep the
   collection names.
3. Run `art/render_all.sh <skin>`, build the app, and pick the skin in
   Settings.

To render a single picture while working on it:

```
flatpak run org.blender.Blender -b art/paper.blend -P art/render_skin.py -- art/out/paper rain_day
```
