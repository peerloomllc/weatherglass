# Weatherglass for iPhone

A SwiftUI app with WidgetKit widgets. It uses the same forecast sources and
the same skins as the Android app:

- `Weatherglass/skins.json` is written from the Android `Skin.kt` by
  `tools/skins_json.py`. Run it after changing a skin.
- The skin pictures are the Android files in
  `app/src/main/res/drawable-nodpi`, copied into the app as they are.
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
Simulator. Debug builds take `-seedPlace "Name,lat,lon"` and `-seedSkin id`
as launch arguments, to start with a place without tapping.

## Not yet

Opening animations, alerts as notifications, the map, the daily skin,
weather sharing and the About page are Android-only so far.
