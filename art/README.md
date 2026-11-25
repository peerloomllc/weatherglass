# Skin art

Each skin can have its own picture for every weather type, made in Blender.
Pictures a skin does not have fall back to the built-in line icons.

## Files

| File | What it does |
| --- | --- |
| `<skin>.blend` | The skin's scene. Open it in Blender and edit by hand |
| `build_paper.py` | Builds the starter Paper cut scene from scratch (overwrites `paper.blend`) |
| `render_skin.py` | Renders a scene into 18 transparent PNGs in `out/<skin>/` |
| `install_skin.sh` | Turns those PNGs into WebP in the app (`res/drawable-nodpi/skin_<skin>_*.webp`) |
| `render_all.sh` | Both steps: `art/render_all.sh paper` |

Rendering all 18 takes about 90 seconds on the GPU.

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
