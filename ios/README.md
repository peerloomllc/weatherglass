# Weatherglass for iPhone

A SwiftUI app with WidgetKit widgets. It uses the same forecast sources and
the same skins as the Android app:

- `Weatherglass/skins.json` is written from the Android `Skin.kt` by
  `tools/skins_json.py`. Run it after changing a skin.
- The skin pictures, opening clips and map outlines are the Android files
  in `app/src/main/res/drawable-nodpi`, `app/src/main/res/raw` and
  `app/src/main/assets/basemap.bin`, copied into the app as they are.
  The widget extension reads them from the app's bundle.
- `Shared/` is compiled into both the app and the widgets. They share
  settings, places and saved forecasts through the app group
  `group.com.peerloom.weatherglass`.

## Build

On the Mac Mini, after copying the repo over (`ios/` and
`app/src/main/res/drawable-nodpi/` are all it needs):

```
cd ios && xcodegen && xcodebuild -project Weatherglass.xcodeproj -scheme Weatherglass -sdk iphonesimulator -destination "generic/platform=iOS Simulator" -derivedDataPath build -allowProvisioningUpdates build
```

The app has to be signed (`-allowProvisioningUpdates`) for the widgets to
see its data, also on the Simulator. Test on the `Weatherglass-iOS27`
Simulator. Debug builds take launch arguments for testing without taps:
`-seedPlace "Name,lat,lon"`, `-seedSkin id`, and `-testAlerts YES` (turns on
freeze tonight at 30 °C and runs the background check after 4 seconds, so
its notification fires in the evening, place time).

## On the iPhone over USB

`ios/device-install.sh` builds on the Mac Mini and installs on the iPhone
plugged into the Linux box, signed with the "Weatherglass Development" and
"Weatherglass Widgets Development" profiles (they list the phone).

## TestFlight

`ios/testflight.sh` copies the code to the Mac Mini, archives a Release
build, signs it with the "Weatherglass AppStore" and "Weatherglass Widgets
AppStore" profiles and uploads it with the `asc` CLI. The build number comes
from App Store Connect. The App Store name is "Weatherglass Weather" (app
ID 6839877608), since "Weatherglass" was taken. New builds still need adding
to the "Internal Testers" group:
`asc builds add-groups --app 6839877608 --latest --group abc2b20b-641a-46dc-9183-0d75dbb37484`.

## Differences from Android

- Notifications (severe weather and freeze tonight) come from iOS
  background refresh, which iOS runs when it chooses, so they can be late.
- No "rain starting soon" alert: it needs a check every 15 minutes, which
  iOS does not allow.
- No weather sharing with other apps; iOS has no equivalent.
