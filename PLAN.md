# Weatherglass - plan

A simple, fast Android weather app with home screen widgets. No ads, no
accounts, no tracking. Built for Tim first, maybe released later on Zapstore
and GitHub.

Status: plan only, nothing built. Written 2026-11-25.

## Goal

Open the app or glance at the widget and know what the weather is doing now,
over the next few hours and over the next week. Nothing else competes for
attention.

## Version 1 features

1. **Now:** temperature, feels like, condition icon, today's high and low.
2. **Next 48 hours, hour by hour:** temperature, rain chance and rain amount.
3. **Next 10 days:** one row per day with high, low, icon and rain chance,
   with a bar showing the day's temperature range.
4. **Rain timing:** a single line such as "Rain starting in about 20 minutes",
   from the 15-minute forecast. Hidden when no rain is coming.
5. **Severe weather alerts:** shown at the top of the screen and sent as a
   notification. These are the only notifications the app ever sends, and
   they can be switched off.
6. **Details:** wind speed and direction, humidity, UV, sunrise and sunset.
7. **Locations:** current location (rough location permission only, checked
   when the app or widget refreshes, never in the background all day) plus
   saved places found by city search.
8. **Widgets:** small (temperature and icon), medium (now plus the next few
   hours) and large (now plus several days). Tapping opens the app.
9. **Settings:** °F or °C, wind units, 12 or 24 hour time, skin, alerts on
   or off. One screen.

## Widget options (added 2026-11-25)

At least one widget style shows the date and time alongside the weather.
People can choose what each widget shows (clock, date, place, high and low,
rain chance, next hours, next days), the way many weather apps allow.

## Later (version 2 and on)

- Rain radar map. The heaviest feature to build, and the data costs money
  or needs a key at most sources.
- Air quality and pollen, each as a toggle.
- More skins for the dashboard and widgets.
- Alerts outside the US (MeteoAlarm covers Europe).

## Never

Ads, analytics, accounts, news or video, "lifestyle" scores, daily forecast
notifications, background location tracking and heavy animated backgrounds.

## Speed rules

- Open straight to the last saved forecast. Refresh quietly behind it. No
  loading spinner on launch.
- Widgets refresh every 30 to 60 minutes, and also when the app refreshes.
- One scrolling screen. No tabs or menus to dig through.
- Keep the app small, aiming for under 10 MB.

## Weather data

| Source | Gives us | Cost | Catch |
| --- | --- | --- | --- |
| Open-Meteo | Forecast for anywhere, 15-minute rain, city search, air quality | Free, no key | Free tier is non-commercial and needs credit shown. A free app with no ads should qualify, but confirm with them before a public release |
| US National Weather Service | Official US severe weather alerts | Free, no key | US only |
| MET Norway (Yr) | Backup forecast source | Free | Must credit them and send an app name with each request |

Each phone asks the source directly. There is no server of ours in between,
so nothing to run and nothing that sees users' locations.

## How it gets built

Plain Kotlin with Jetpack Compose, using Android's own widget tools (Glance)
and background refresh (WorkManager). Our other apps use Expo, but Expo
handles widgets poorly, and plain Kotlin keeps the app small and quick.

Skins are a set of colors, fonts and icon styles shared by the app and its
widgets, so one switch changes both.

Testing follows the usual order: emulator first, then the TCL.

## What is already on Zapstore

Checked 2026-11-25. About 20 weather apps are listed. The ones closest to this
idea:

| App | What it is |
| --- | --- |
| Breezy Weather | Full-featured open-source app with 50+ data sources, many widgets, alerts, air quality and pollen. The heavy option |
| OSS Weather | Lightweight, privacy-first, with radar (MapTiler), minute and hourly forecasts and widgets. The closest match to this plan |
| Weather (Vayun Mathur) | Material You look, Open-Meteo data, widgets |
| Duffezerie Weather | Lightweight, styled after Apple Weather, Open-Meteo data |
| Overmorrow | Design-focused open-source app |
| QuickWeather | Small and simple |
| WeatherGrid | Widget only: a 3-hour forecast grid you tap to switch between rain, sun and wind |
| Weather Forecast USA | US forecasts plus official watches and warnings |
| Weather Radar | US National Weather Service radar images only |

So "no ads, open source, uses Open-Meteo" is already covered several times
over. To stand out, this app has to be the simplest to read at a glance and
offer the best skins for the dashboard and widgets. WeatherGrid's tap to
switch what the widget shows is worth borrowing.

## Skins

Custom skins for the dashboard and widgets are the main thing that sets this
app apart. Art made in Blender where it fits.

Tim's picks: Retro-future, 8-bit, Kurosawa, Anime.

More ideas (2026-11-25):

- Retro and tech: CRT Terminal, Vaporwave, round gauge dial (our own design),
  Calculator / LCD watch, Teletext.
- Art and print: Ukiyo-e woodblock, Ink wash (sumi-e), Bauhaus, Art Deco,
  Risograph, Blueprint.
- Cozy and hand-made: Watercolor, Paper cut / diorama, Claymation, Knitted /
  felt, Chalkboard.
- Places and moods: Ship's barometer, Field journal, Noir, Lo-fi bedroom
  window, Terrarium.
- Games and fun: 16-bit RPG overworld, Tabletop dice sheet, Isometric town,
  Minimal Mono (the plain default).

How skins get made:

- Widgets cannot play live 3D, so each skin is a set of pictures rendered
  ahead of time: about 10 weather types times day and night, roughly 20
  images per skin. The app can also use short looping clips.
- Skins built around one small scene (diorama, terrarium, isometric town,
  window view) are cheapest: each weather type is just a new render of the
  same scene.

## Decided (2026-11-25)

- Android only. No iPhone version planned.
- All skins free. Zaps and donations welcome, no paid skins.
- Tapping a widget opens the app.
- Tim makes the skin art in Blender.
- Released under the PeerLoom name, with a website page and privacy policy.
- Open source.
- Severe weather alerts are US only at launch.
- Android 12 and newer.
- Version 1 skins: Minimal Mono (default), Paper cut diorama, 8-bit and
  Retro-future.
- Radar: decide after version 1 is in daily use.
- Name: Weatherglass (an old word for a barometer).

## Open questions

- Confirm with Open-Meteo that a free, ad-free app fits their free tier.
