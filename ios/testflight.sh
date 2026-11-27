#!/bin/bash
# Archive the iPhone app and upload it to TestFlight. Run on the Linux box:
#   ios/testflight.sh [marketing version]      (default: MARKETING_VERSION in project.yml)
# It copies ios/ and the Android art the app uses to the Mac Mini, builds
# there and uploads with the asc CLI. The build number comes from App Store
# Connect, so every upload is higher than the last.
set -euo pipefail
MAC=tims-mac-mini.local
APP_ID=6839877608 # "Weatherglass Weather" in App Store Connect
cd "$(dirname "$0")/.."
VERSION=${1:-$(grep -m1 MARKETING_VERSION ios/project.yml | grep -oE '[0-9.]+')}

rsync -az --delete --exclude build/ --exclude Weatherglass.xcodeproj/ --relative \
  ios/ app/src/main/res/drawable-nodpi/ app/src/main/res/raw/ app/src/main/assets/ "$MAC:peerloomllc/weather/"

ssh "$MAC" APP_ID="$APP_ID" VERSION="$VERSION" 'bash -s' <<'REMOTE'
set -euo pipefail
export PATH=/opt/homebrew/bin:$PATH
cd ~/peerloomllc/weather/ios
xcodegen -q
BUILD=$(asc builds next-build-number --app "$APP_ID" --platform IOS 2>/dev/null | python3 -c 'import sys,json; print(int(json.load(sys.stdin)["nextBuildNumber"]))' 2>/dev/null || echo 1)
echo "Version $VERSION, build $BUILD"
# The distribution key lives in a keychain codesign can use over SSH.
security unlock-keychain -p "" ~/Library/Keychains/buildkey.keychain
security list-keychains -s ~/Library/Keychains/buildkey.keychain ~/Library/Keychains/login.keychain-db /Library/Keychains/System.keychain
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "" ~/Library/Keychains/buildkey.keychain >/dev/null
# Homebrew's rsync breaks Xcode's IPA packaging; keep it off PATH for xcodebuild.
XPATH=$(printf '%s' "$PATH" | sed 's|/opt/homebrew/bin:||g')
rm -rf build/Weatherglass.xcarchive build/export
PATH="$XPATH" xcodebuild -project Weatherglass.xcodeproj -scheme Weatherglass -configuration Release \
  -destination generic/platform=iOS -archivePath build/Weatherglass.xcarchive \
  MARKETING_VERSION="$VERSION" CURRENT_PROJECT_VERSION="$BUILD" \
  OTHER_CODE_SIGN_FLAGS="--keychain $HOME/Library/Keychains/buildkey.keychain" archive 2>&1 \
  | tee /tmp/weatherglass-archive.log | grep -E "error:|ARCHIVE (SUCCEEDED|FAILED)" || true
[ -d build/Weatherglass.xcarchive ] || { echo "Archive failed, see /tmp/weatherglass-archive.log on the Mac"; exit 1; }
cat > build/ExportOptions.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>app-store-connect</string>
  <key>teamID</key><string>G79ALD29NA</string>
  <key>signingStyle</key><string>manual</string>
  <key>signingCertificate</key><string>Apple Distribution</string>
  <key>provisioningProfiles</key><dict>
    <key>com.peerloom.weatherglass</key><string>Weatherglass AppStore</string>
    <key>com.peerloom.weatherglass.widgets</key><string>Weatherglass Widgets AppStore</string>
  </dict>
  <key>uploadSymbols</key><false/>
</dict></plist>
PLIST
PATH="$XPATH" xcodebuild -exportArchive -archivePath build/Weatherglass.xcarchive -exportPath build/export \
  -exportOptionsPlist build/ExportOptions.plist 2>&1 | grep -E "error|EXPORT (SUCCEEDED|FAILED)" || true
IPA=$(ls build/export/*.ipa 2>/dev/null | head -1)
[ -n "$IPA" ] || { echo "Export failed"; exit 1; }
echo "Uploading $IPA ($(du -h "$IPA" | cut -f1))"
ASC_UPLOAD_TIMEOUT=1200s asc builds upload --app "$APP_ID" --ipa "$IPA"
REMOTE
