#!/usr/bin/env bash
# Render a skin's .blend into its 18 pictures and install them in the app.
#   art/render_all.sh paper          (uses art/paper.blend)
set -euo pipefail
skin=${1:?usage: render_all.sh <skin>}
here=$(cd "$(dirname "$0")" && pwd)
flatpak run org.blender.Blender -b "$here/$skin.blend" -P "$here/render_skin.py" -- "$here/out/$skin" 2>&1 | grep -E 'RENDERED|WARNING: no|Error' || true
"$here/install_skin.sh" "$skin"
# Skins that draw the weather inside a container also get a small-size set
# with the container hidden (see render_skin.py --mini).
case $skin in
  terrarium | dice | gauge | iso)
    flatpak run org.blender.Blender -b "$here/$skin.blend" -P "$here/render_skin.py" -- "$here/out/${skin}_mini" --mini 2>&1 | grep -E 'RENDERED|Error' || true
    "$here/install_skin.sh" "$skin" mini ;;
esac
