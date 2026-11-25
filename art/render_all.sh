#!/usr/bin/env bash
# Render a skin's .blend into its 18 pictures and install them in the app.
#   art/render_all.sh paper          (uses art/paper.blend)
set -euo pipefail
skin=${1:?usage: render_all.sh <skin>}
here=$(cd "$(dirname "$0")" && pwd)
flatpak run org.blender.Blender -b "$here/$skin.blend" -P "$here/render_skin.py" -- "$here/out/$skin" 2>&1 | grep -E 'RENDERED|WARNING: no|Error' || true
"$here/install_skin.sh" "$skin"
