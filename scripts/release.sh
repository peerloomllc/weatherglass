#!/usr/bin/env bash
# Release Weatherglass: build a signed APK, then publish it to GitHub, Zapstore
# and a Nostr announcement, and send the iPhone app to the App Store.
#
#   scripts/release.sh            next version (v1.0.0 first, then a patch bump)
#   scripts/release.sh v1.2.0     a given version
#
# Follows ../RELEASE-PIPELINE.md where it applies. Weatherglass is a plain
# Gradle app plus a native iPhone app (ios/), with no desktop, seeder or Play
# builds, so those steps are absent, and the numbering below matches the
# canonical order. The
# version comes from the tag (passed to Gradle as APP_VERSION), so there are
# no version files to bump and nothing is committed to main.
#
# Needs scripts/.env (gitignored):
#   KEYSTORE_FILE       release keystore (default ~/keystore.jks)
#   KEYSTORE_PASSWORD   its password
#   KEY_ALIAS           key alias (default weatherglass)
#   KEY_PASSWORD        key password (default: the keystore password)
#   SIGN_WITH           Nostr signer for zsp and the announcement
#   ASC_KEY_ID, ASC_ISSUER_ID, ASC_PRIVATE_KEY_PATH
#                       App Store Connect API key, for the App Store step
#                       (the app's ID, ASC_APP_ID, is in app.conf)
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
PUBLISH_FAILED=false; GITHUB_FAILED=false; ZAPSTORE_FAILED=false; ZAPSTORE_ONLY=false; APP_STORE_FAILED=false
ask() {
  local r
  read -rp "    $1 [Y/n] " r
  case "${r:-y}" in [Yy]*) return 0 ;; *) return 1 ;; esac
}
echo "==> $APP_NAME $RELEASE_TAG (version code $APP_VERSION_CODE)"
ask "Publish to GitHub?" || PUBLISH_GITHUB=false
ask "Publish to Zapstore?" || PUBLISH_ZAPSTORE=false
if _appstore_configured; then
  ask "Send the iPhone app to the App Store?" && PUBLISH_APP_STORE=true
else
  echo "    App Store: not set up (needs the ASC_* keys and the Mac Mini), skipping."
fi
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

# 11: App Store. ios/testflight.sh builds on the Mac Mini and uploads; the
# rest runs here with asc: the version record, What's New, the build and the
# review submission. A failure here never stops the Nostr post.
if $PUBLISH_APP_STORE; then
  echo ""
  echo "==> App Store: building and uploading the iPhone app..."
  release_check_mac_space "${MAC_MINI_HOST:-Tims-Mac-mini.local}"
  IOS_LOG=$(mktemp)
  if ios/testflight.sh "$APP_VERSION" 2>&1 | tee "$IOS_LOG"; then
    IOS_BUILD=$(sed -n -E 's/^Version .*, build ([0-9]+)$/\1/p' "$IOS_LOG" | head -1)
  else
    echo "    ERROR: the iPhone build or upload failed (see above)."
    PUBLISH_FAILED=true; APP_STORE_FAILED=true
  fi
  rm -f "$IOS_LOG"
fi
if $PUBLISH_APP_STORE && ! $APP_STORE_FAILED; then
  if ! _asc_auth_linux; then
    echo "    ERROR: asc could not log in. The build is uploaded; submit it in App Store Connect."
    PUBLISH_FAILED=true; APP_STORE_FAILED=true
  else
    # One open version at a time: use this version's record, rename an unsent
    # one, create one, or stop if Apple is still reviewing an earlier version.
    IOS_VID=$(_asc_version_id "$APP_VERSION")
    if [ -z "$IOS_VID" ]; then
      read -r OPEN_ID OPEN_VER OPEN_STATE < <(asc versions list --app "$ASC_APP_ID" --output json 2>/dev/null | python3 -c "
import json, sys
for v in json.load(sys.stdin).get('data', []):
    a = v['attributes']
    if a['appStoreState'] not in ('READY_FOR_SALE', 'REMOVED_FROM_SALE', 'DEVELOPER_REMOVED_FROM_SALE', 'REPLACED_WITH_NEW_VERSION'):
        print(v['id'], a['versionString'], a['appStoreState']); break
") || true
      case "${OPEN_STATE:-}" in
        PREPARE_FOR_SUBMISSION|DEVELOPER_REJECTED|REJECTED|METADATA_REJECTED|INVALID_BINARY)
          _confirm "Rename the unsent App Store version $OPEN_VER to $APP_VERSION?"
          asc versions update --version-id "$OPEN_ID" --version "$APP_VERSION" >/dev/null && IOS_VID="$OPEN_ID" ;;
        "")
          PRIOR=$(_appstore_latest_version)
          asc versions create --app "$ASC_APP_ID" --version "$APP_VERSION" ${PRIOR:+--copy-metadata-from "$PRIOR"} >/dev/null || true
          IOS_VID=$(_asc_version_id "$APP_VERSION") ;;
        *)
          echo "    Version $OPEN_VER is $OPEN_STATE, so $APP_VERSION cannot be submitted yet."
          echo "    Build $IOS_BUILD is uploaded and in TestFlight. Submit it once $OPEN_VER is out of review." ;;
      esac
    fi
    if [ -n "$IOS_VID" ]; then
      # What's New: the release notes as plain text (not for the first version).
      if [ "$(_appstore_latest_version)" != "" ] && [ "$APP_VERSION" != "1.0.0" ]; then
        META=$(mktemp -d)
        mkdir -p "$META/version/$APP_VERSION"
        python3 - "$REPO_ROOT/release_notes.md" "$META/version/$APP_VERSION/en-US.json" <<'PY'
import json, re, sys
text = open(sys.argv[1]).read()
text = re.sub(r'^#+\s*', '', text, flags=re.M)
text = re.sub(r'\*\*|__|`', '', text)
text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text).strip()
json.dump({'whatsNew': text[:4000]}, open(sys.argv[2], 'w'))
PY
        asc metadata push --app "$ASC_APP_ID" --version "$APP_VERSION" --platform IOS --dir "$META" >/dev/null \
          && echo "    Set What's New from the release notes." \
          || echo "    WARNING: could not set What's New; add it in App Store Connect."
        rm -rf "$META"
      fi
      BUILD_INFO=$(_asc_wait_for_build "$APP_VERSION" "${IOS_BUILD:-}")
      BUILD_ID="${BUILD_INFO%% *}"
      if [ -z "$BUILD_ID" ] || [[ "$BUILD_INFO" != *VALID* ]]; then
        echo "    Build ${IOS_BUILD:-?} is not processed yet (${BUILD_INFO:-not found}). Attach and submit it in App Store Connect."
        PUBLISH_FAILED=true; APP_STORE_FAILED=true
      elif _asc_attach_build "$IOS_VID" "$BUILD_ID"; then
        asc builds update --build-id "$BUILD_ID" --uses-non-exempt-encryption=false >/dev/null 2>&1 || true
        [ -n "${TESTFLIGHT_GROUP:-}" ] && asc builds add-groups --build-id "$BUILD_ID" --group "$TESTFLIGHT_GROUP" >/dev/null 2>&1 || true
        if ask "Submit $APP_VERSION (build ${IOS_BUILD:-?}) for App Store review?"; then
          release_submit_for_review "$IOS_VID" || true
        else
          echo "    Not submitted. The build is attached; submit $APP_VERSION in App Store Connect when ready."
        fi
      else
        PUBLISH_FAILED=true; APP_STORE_FAILED=true
      fi
    fi
  fi
fi

# 12: Nostr announcement.
release_post_nostr "$REPO_ROOT/release_notes.md"

# 13: summary.
release_summary
release_summary_end
