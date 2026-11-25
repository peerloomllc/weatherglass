#!/usr/bin/env bash
# Turn a skin's rendered opening clips into animated WebP in the app.
#   art/install_clip.sh dice
# Takes art/out/<skin>_clip/<weather>_<day|night>/f_0001.png ... and writes
# app/src/main/res/raw/clip_<skin>_<weather>_<day|night>.webp
# Every frame is cropped to the last frame's outline and sized like the
# still pictures (install_skin.sh), so the clip ends exactly on the still.
set -euo pipefail
skin=${1:?usage: install_clip.sh <skin>}
quality=${QUALITY:-60}
size=${SIZE:-240}  # a little under the stills (300): it only shows for 1.5 seconds
here=$(cd "$(dirname "$0")" && pwd)
src="$here/out/${skin}_clip"
dst="$here/../app/src/main/res/raw"
mkdir -p "$dst"
fit=$((size * 284 / 300))
case $skin in
  pixel | teletext | rpg) filt=(-filter point) ;;
  *) filt=() ;;
esac
n=0
for d in "$src"/*/; do
  pic=$(basename "$d")
  last=$(ls "$d"f_*.png | tail -1)
  box=$(magick "$last" -format "%@" info:)
  magick "$d"f_*.png -crop "$box" +repage "${filt[@]}" -resize "${fit}x${fit}" -gravity center -background none \
    -extent "${size}x${size}" -set delay 8 -loop 1 -define webp:lossless=false -quality "$quality" \
    -define webp:alpha-quality=80 "$dst/clip_${skin}_${pic}.webp"
  n=$((n+1))
done
# Same as install_skin.sh: drop night clips identical to the day ones.
for f in "$dst"/clip_"${skin}"_*_night.webp; do
  [ -e "$f" ] || continue
  if cmp -s "$f" "${f/_night/_day}"; then rm "$f"; n=$((n-1)); fi
done
echo "installed $n clips for $skin ($(du -ch "$dst"/clip_"${skin}"_*.webp | tail -1 | cut -f1) total)"
