#!/usr/bin/env bash
# Copy a skin's rendered pictures into the app as WebP.
#   art/install_skin.sh paper
# Takes art/out/<skin>/<weather>_<day|night>.png and writes
# app/src/main/res/drawable-nodpi/skin_<skin>_<weather>_<day|night>.webp
# at 360px, large enough for the app's biggest icon (120dp) on sharp screens.
set -euo pipefail
skin=${1:?usage: install_skin.sh <skin>}
here=$(cd "$(dirname "$0")" && pwd)
src="$here/out/$skin"
dst="$here/../app/src/main/res/drawable-nodpi"
mkdir -p "$dst"
# Pixel art is scaled with hard edges and saved lossless so the cells stay
# sharp and the colors exact. Everything else is smoothed and saved lossy.
case $skin in
  pixel | teletext) look=(-filter point -resize 340x340); save=(-define webp:lossless=true) ;;
  *) look=(-resize 340x340); save=(-define webp:lossless=false -quality 88 -define webp:alpha-quality=100) ;;
esac
n=0
for f in "$src"/*_day.png "$src"/*_night.png; do
  [ -e "$f" ] || continue
  base=$(basename "$f" .png)
  magick "$f" -trim +repage "${look[@]}" -gravity center -background none -extent 360x360 \
    "${save[@]}" "$dst/skin_${skin}_${base}.webp"
  n=$((n+1))
done
echo "installed $n pictures for $skin ($(du -ch "$dst"/skin_"${skin}"_*.webp | tail -1 | cut -f1) total)"
