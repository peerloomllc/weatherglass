#!/usr/bin/env bash
# Release Weatherglass: build a signed APK, then publish it to GitHub, Zapstore
# and a Nostr announcement.
#
#   scripts/release.sh            next version (v1.0.0 first, then a patch bump)
#   scripts/release.sh v1.2.0     a given version
#
# Follows ../RELEASE-PIPELINE.md where it applies. Weatherglass is a plain
# Gradle app with no desktop, seeder, Play or App Store builds, so those steps
# are absent, and the numbering below matches the canonical order. The
# version comes from the tag (passed to Gradle as APP_VERSION), so there are
# no version files to bump and nothing is committed to main.
#
# Needs scripts/.env (gitignored):
#   KEYSTORE_FILE       release keystore (default ~/keystore.jks)
#   KEYSTORE_PASSWORD   its password
#   KEY_ALIAS           key alias (default weatherglass)
#   KEY_PASSWORD        key password (default: the keystore password)
#   SIGN_WITH           Nostr signer for zsp and the announcement
# Shared steps come from ../peerloom-release/release-lib.sh.
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT"

# A1: settings, then secrets.
set -a
source scripts/app.conf
[ -f scripts/.env ] && source scripts/.env
set +a
source "$REPO_ROOT/../peerloom-release/release-lib.sh"
release_lib_require_current

# A3: the release tag.
RELEASE_TAG="${1:-}"
if [ -z "$RELEASE_TAG" ]; then
  last=$(git tag -l 'v*' --sort=-v:refname | head -1)
  if [ -z "$last" ]; then
    RELEASE_TAG="v1.0.0"
  else
    IFS=. read -r _ma _mi _pa <<<"${last#v}"
    RELEASE_TAG="v${_ma}.${_mi}.$((_pa + 1))"
  fi
fi
[[ "$RELEASE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Error: tag must look like v1.2.3"; exit 1; }
APP_VERSION="${RELEASE_TAG#v}"
IFS=. read -r _ma _mi _pa <<<"$APP_VERSION"
APP_VERSION_CODE=$((_ma * 1000000 + _mi * 1000 + _pa))
export APP_VERSION APP_VERSION_CODE

# A5: credentials.
: "${KEYSTORE_PASSWORD:?Set KEYSTORE_PASSWORD in scripts/.env}"
KEYSTORE_FILE="${KEYSTORE_FILE:-$HOME/keystore.jks}"
KEY_ALIAS="${KEY_ALIAS:-$KEY_ALIAS_DEFAULT}"
KEY_PASSWORD="${KEY_PASSWORD:-$KEYSTORE_PASSWORD}"
[ -f "$KEYSTORE_FILE" ] || { echo "Error: keystore not found at $KEYSTORE_FILE"; exit 1; }
export KEYSTORE_FILE KEYSTORE_PASSWORD KEY_ALIAS KEY_PASSWORD

# Release from an up-to-date, clean main only.
[ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || { echo "Error: release from main"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "Error: uncommitted changes"; exit 1; }
git fetch -q origin main
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "Error: main is not the same as origin/main"; exit 1; }
if git rev-parse -q --verify "refs/tags/$RELEASE_TAG" >/dev/null; then
  echo "Error: tag $RELEASE_TAG already exists"; exit 1
fi

# A7: destinations.
PUBLISH_GITHUB=true; PUBLISH_ZAPSTORE=true; PUBLISH_NOSTR=true
PUBLISH_PLAY=false; PUBLISH_APP_STORE=false; PUBLISH_DESKTOP=false; PUBLISH_LINUX=false
PUBLISH_FAILED=false; GITHUB_FAILED=false; ZAPSTORE_FAILED=false; ZAPSTORE_ONLY=false
ask() {
  local r
  read -rp "    $1 [Y/n] " r
  case "${r:-y}" in [Yy]*) return 0 ;; *) return 1 ;; esac
}
echo "==> $APP_NAME $RELEASE_TAG (version code $APP_VERSION_CODE)"
ask "Publish to GitHub?" || PUBLISH_GITHUB=false
ask "Publish to Zapstore?" || PUBLISH_ZAPSTORE=false
ask "Post a Nostr announcement?" || PUBLISH_NOSTR=false
_confirm "Release tag will be $RELEASE_TAG - proceed with build?"

# 1: verify gate.
echo "==> Running the unit tests..."
./gradlew -q testDebugUnitTest

# 3: signed release APK.
echo "==> Building the signed release APK..."
./gradlew -q clean assembleRelease
BUILT=app/build/outputs/apk/release/app-release.apk
[ -f "$BUILT" ] || { echo "Error: no signed APK (is the keystore set up?)"; exit 1; }
APKSIGNER=$(ls -d "${ANDROID_HOME:-$HOME/Android/Sdk}"/build-tools/*/ | sort -V | tail -1)apksigner
"$APKSIGNER" verify --print-certs "$BUILT" | grep -m1 "Signer #1 certificate DN" || { echo "Error: APK is not signed"; exit 1; }

# 4: versioned name.
APK_NAME="${ARTIFACT_PREFIX}-${RELEASE_TAG}.apk"
cp "$BUILT" "$APK_NAME"
APK_SIZE=$(du -sh "$APK_NAME" | cut -f1)
AAB_NAME=""
echo "==> Built APK: $APK_NAME ($APK_SIZE)"

# 4e: checksum (asks to continue).
release_write_checksums

# 5: release notes (asks whether they look good).
release_write_notes

_confirm "APK ($APK_SIZE) ready to publish?"

# 6b: push the tag (the point of no return).
release_push_and_tag
REPO_SLUG="${REPO_SLUG:-$(_remote_slug)}"

# 7: GitHub release.
if $PUBLISH_GITHUB; then
  _confirm "Create public GitHub release $RELEASE_TAG with $APK_NAME and its checksum?"
  if gh release create "$RELEASE_TAG" "$APK_NAME" "$APK_NAME.sha256" -R "$REPO_SLUG" \
      --title "$RELEASE_TAG" --notes-file release_notes.md; then
    echo "    Published the GitHub release."
  else
    echo "    ERROR: GitHub release failed."
    GITHUB_FAILED=true; PUBLISH_FAILED=true
  fi
fi

# 8-9: Zapstore.
release_install_zsp
release_publish_zapstore "$REPO_ROOT/$APK_NAME" "$REPO_ROOT/release_notes.md"

# 12: Nostr announcement.
release_post_nostr "$REPO_ROOT/release_notes.md"

# 13: summary.
release_summary
release_summary_end
