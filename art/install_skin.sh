#!/usr/bin/env bash
# Copy a skin's rendered pictures into the app as WebP.
#   art/install_skin.sh paper
#   art/install_skin.sh dice mini     (the small-size set, from out/dice_mini)
# Takes art/out/<skin>/<weather>_<day|night>.png and writes
# app/src/main/res/drawable-nodpi/skin_<skin>_<weather>_<day|night>.webp
# (with "mini", from out/<skin>_mini to ..._<day|night>_mini.webp)
# at 300px: the app's biggest icon is 120dp, which is 315px on a Pixel 9 and
# 240px on the TCL, so 300px stays sharp without wasting space.
set -euo pipefail
skin=${1:?usage: install_skin.sh <skin> [mini]}
here=$(cd "$(dirname "$0")" && pwd)
suffix=${2:+_$2}
src="$here/out/$skin$suffix"
dst="$here/../app/src/main/res/drawable-nodpi"
mkdir -p "$dst"
# Pixel art is scaled with hard edges and saved lossless so the cells stay
# sharp and the colors exact. Everything else is smoothed and saved lossy.
# Transparency costs more than color, so its quality is set a little lower
# too (90 instead of 100): edges stay clean, grainy skins shrink a lot.
case $skin in
  pixel | teletext | rpg) look=(-filter point -resize 284x284); save=(-define webp:lossless=true) ;;
  *) look=(-resize 284x284); save=(-define webp:lossless=false -quality 85 -define webp:alpha-quality=90) ;;
esac
n=0
for f in "$src"/*_day.png "$src"/*_night.png; do
  [ -e "$f" ] || continue
  base=$(basename "$f" .png)
  magick "$f" -trim +repage "${look[@]}" -gravity center -background none -extent 300x300 \
    "${save[@]}" "$dst/skin_${skin}_${base}${suffix}.webp"
  n=$((n+1))
done
# Most weathers look the same by day and night. Keep only the day picture
# of those; the app falls back to it at night.
for f in "$dst"/skin_"${skin}"_*_night"${suffix}".webp; do
  [ -e "$f" ] || continue
  if cmp -s "$f" "${f/_night/_day}"; then rm "$f"; n=$((n-1)); fi
done
echo "installed $n pictures for $skin$suffix ($(du -ch "$dst"/skin_"${skin}"_*"${suffix}".webp | tail -1 | cut -f1) total)"
