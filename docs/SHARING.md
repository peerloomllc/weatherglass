# Reading Weatherglass forecasts from your app

Weatherglass can share its forecasts with other apps on the same phone, so
those apps need no location permission and no weather service of their own.
It is off until the person switches on **Settings > Share weather > Other
apps**, and each app has to be allowed by the person. Nothing leaves the
phone.

## 1. Ask for the permission

```xml
<uses-permission android:name="com.peerloom.weatherglass.READ_WEATHER" />
```

It is a runtime permission, so request it like any other:

```kotlin
requestPermissions(arrayOf("com.peerloom.weatherglass.READ_WEATHER"), 1)
```

## 2. Read the forecasts

```kotlin
val uri = Uri.parse("content://com.peerloom.weatherglass.weather/forecast")
contentResolver.query(uri, null, null, null, null)?.use { c ->
    while (c.moveToNext()) {
        val place = c.getString(c.getColumnIndexOrThrow("place"))
        val json = c.getString(c.getColumnIndexOrThrow("json"))
    }
}
```

One row per saved place that has a forecast. No rows while sharing is off.

| Column | Type | What it is |
| --- | --- | --- |
| `place` | text | The place's name, e.g. "Hialeah" |
| `lat`, `lon` | real | Where the place is (the forecast point, not a GPS fix) |
| `is_current` | int | 1 for the "My location" place |
| `selected` | int | 1 for the place the person is looking at in Weatherglass |
| `fetched_at` | int | When the forecast was downloaded, milliseconds since 1970 |
| `json` | text | The whole forecast, described below |

## 3. The forecast JSON

Always metric: °C, km/h, mm. Times are local to the place, as ISO text
without a zone (`2026-11-26T14:00`); `utcOffsetSeconds` turns them into UTC.
Weather codes are WMO codes, as used by Open-Meteo.

```json
{
  "place": { "name": "Hialeah", "lat": 25.86, "lon": -80.28, "region": "Florida", "isCurrent": false },
  "fetchedAt": 1764163200000,
  "utcOffsetSeconds": -18000,
  "current": { "time": "2026-11-26T09:00", "tempC": 23.4, "feelsC": 25.1, "humidity": 79,
               "windKmh": 12.0, "windDir": 90, "code": 2, "isDay": true },
  "hours": [ { "time": "2026-11-26T10:00", "tempC": 24.0, "rainChance": 10, "rainMm": 0.0, "code": 2, "isDay": true } ],
  "days": [ { "date": "2026-11-26", "code": 61, "maxC": 27.0, "minC": 19.0, "rainChance": 60,
              "sunrise": "2026-11-26T06:52", "sunset": "2026-11-26T17:30", "uvMax": 6.5, "sunHours": 7.5 } ],
  "quarters": [ { "time": "2026-11-26T09:15", "rainMm": 0.0 } ],
  "alerts": [ { "id": "...", "event": "Flood Watch", "headline": "...", "severity": "Moderate",
                "ends": "2026-11-26T18:00:00-05:00", "description": "..." } ]
}
```

`hours` covers the next 48 hours, `days` the next 10, and `quarters` the
15-minute rain amounts for the next few hours. `alerts` are US National
Weather Service alerts and are empty elsewhere. Fields may be added later;
ignore the ones you do not know.

## 4. Hear about new forecasts

After each new forecast for the selected place, Weatherglass sends the
broadcast `com.peerloom.weatherglass.ACTION_WEATHER_UPDATED`, delivered
only to apps holding the permission. Register for it while your app runs:

```kotlin
registerReceiver(receiver, IntentFilter("com.peerloom.weatherglass.ACTION_WEATHER_UPDATED"), RECEIVER_EXPORTED)
```

Weatherglass refreshes about once an hour in the background, every 15
minutes when its rain alert is on, and whenever it is opened.

## Gadgetbridge

Separately, **Settings > Share weather > Watch** sends each forecast to
Gadgetbridge in its own `WeatherGz` format, so watches connected through it
show the same weather.
