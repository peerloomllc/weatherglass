#!/usr/bin/env bash
# Render and install the opening clips for one skin, or all of them.
#   art/render_clips.sh            every skin in the list below
#   art/render_clips.sh paper      just one
# Each skin's animation style is set here (see animate_clip.py for what
# each style does).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
declare -A STYLE=(
  [paper]=popup [pixel]=steps [rpg]=steps [teletext]=steps [crt]=crt
  [vapor]=glitch [riso]=glitch [lcd]=blink [anime]=smooth [bauhaus]=smooth
  [barometer]=smooth [terrarium]=smooth [iso]=smooth [ukiyoe]=stagger
  [blueprint]=stagger [chalk]=stagger [journal]=stagger [ink]=bloom
  [watercolor]=bloom [noir]=film [kurosawa]=film [felt]=clay [clay]=clay
  [deco]=glow [lofi]=glow [retro]=glow [dice]=dice [gauge]=gauge
  [coin]=coin [blocks]=mine [whitepaper]=stagger [laser]=laser
)
skins=("${@:-${!STYLE[@]}}")
for skin in "${skins[@]}"; do
  style=${STYLE[$skin]:?no style for $skin}
  rm -rf "$here/out/${skin}_clip"
  flatpak run org.blender.Blender -b "$here/$skin.blend" -P "$here/animate_clip.py" -- "$here/out/${skin}_clip" "$style" 2>&1 \
    | grep -E 'Traceback|Error' || true
  rm -f "$here/../app/src/main/res/raw/clip_${skin}_"*.webp
  "$here/install_clip.sh" "$skin"
done
