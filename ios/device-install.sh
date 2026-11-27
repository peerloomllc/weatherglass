#!/bin/bash
# Build the iPhone app on the Mac Mini and install it on the iPhone plugged
# into this Linux box over USB, signed with the development profiles
# ("Weatherglass Development" and "Weatherglass Widgets Development", which
# list the phone). No TestFlight needed.
#   ios/device-install.sh
set -euo pipefail
MAC=tims-mac-mini.local
cd "$(dirname "$0")/.."
LOCAL_IPA=/tmp/weatherglass-dev.ipa
idevice_id -l | grep -q . || { echo "No iPhone on USB (idevice_id -l is empty)"; exit 1; }

rsync -az --delete --exclude build/ --exclude Weatherglass.xcodeproj/ --relative \
  ios/ app/src/main/res/drawable-nodpi/ app/src/main/res/raw/ app/src/main/assets/ "$MAC:peerloomllc/weather/"

ssh "$MAC" 'bash -s' <<'REMOTE'
set -euo pipefail
export PATH=/opt/homebrew/bin:$PATH
cd ~/peerloomllc/weather/ios
xcodegen -q
security unlock-keychain -p "" ~/Library/Keychains/buildkey.keychain
security list-keychains -s ~/Library/Keychains/buildkey.keychain ~/Library/Keychains/login.keychain-db /Library/Keychains/System.keychain
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "" ~/Library/Keychains/buildkey.keychain >/dev/null
XPATH=$(printf '%s' "$PATH" | sed 's|/opt/homebrew/bin:||g')
rm -rf build/Dev.xcarchive build/dev-export
# Archive as for the App Store, then export re-signed for development.
PATH="$XPATH" xcodebuild -project Weatherglass.xcodeproj -scheme Weatherglass -configuration Release \
  -destination generic/platform=iOS -archivePath build/Dev.xcarchive \
  OTHER_CODE_SIGN_FLAGS="--keychain $HOME/Library/Keychains/buildkey.keychain" archive 2>&1 \
  | tee /tmp/weatherglass-dev-archive.log | grep -E "error:|ARCHIVE (SUCCEEDED|FAILED)" || true
[ -d build/Dev.xcarchive ] || { echo "Archive failed, see /tmp/weatherglass-dev-archive.log on the Mac"; exit 1; }
cat > build/DevExport.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>development</string>
  <key>teamID</key><string>G79ALD29NA</string>
  <key>signingStyle</key><string>manual</string>
  <key>signingCertificate</key><string>Apple Development</string>
  <key>provisioningProfiles</key><dict>
    <key>com.peerloom.weatherglass</key><string>Weatherglass Development</string>
    <key>com.peerloom.weatherglass.widgets</key><string>Weatherglass Widgets Development</string>
  </dict>
</dict></plist>
PLIST
PATH="$XPATH" xcodebuild -exportArchive -archivePath build/Dev.xcarchive -exportPath build/dev-export \
  -exportOptionsPlist build/DevExport.plist 2>&1 | grep -E "error|EXPORT (SUCCEEDED|FAILED)" || true
ls build/dev-export/*.ipa >/dev/null
REMOTE

scp -q "$MAC:peerloomllc/weather/ios/build/dev-export/Weatherglass.ipa" "$LOCAL_IPA"
ideviceinstaller install "$LOCAL_IPA" 2>&1 | tail -2
