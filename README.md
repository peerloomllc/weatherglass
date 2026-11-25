# Weatherglass

A simple, fast Android weather app with home screen widgets. No ads, no
account, no tracking. Skins change the look of the app and widgets together.

- Weather data by [Open-Meteo.com](https://open-meteo.com) (CC BY 4.0)
- US severe weather alerts from the National Weather Service
- Rough location only, from Android itself, and only while the app is open

Android 12 and newer.

## Build

```
./gradlew :app:assembleDebug
./gradlew :app:testDebugUnitTest
```

The debug build installs as `com.peerloom.weatherglass.debug`, alongside a
release install.

## Skin art

Skin pictures are made in Blender and rendered by script. See
`art/README.md`. Any picture a skin lacks falls back to the built-in line
icon in the skin's colors. See `PLAN.md` for the plan and decisions.
