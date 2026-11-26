package com.peerloom.weatherglass.data

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import kotlinx.serialization.Serializable
import java.io.ByteArrayOutputStream
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.util.zip.GZIPOutputStream
import kotlin.math.roundToInt

// Sharing the forecast with other apps on the phone, both off until switched
// on in Settings. Nothing leaves the phone:
//
// - Gadgetbridge (the open-source smartwatch app) gets the forecast in its
//   own format after every refresh, so a connected watch shows it.
// - Apps the person allows can read the saved forecasts through
//   WeatherProvider, and hear about new ones from a broadcast. See
//   docs/SHARING.md for the format.

object Share {
    const val GADGETBRIDGE_ACTION = "nodomain.freeyourgadget.gadgetbridge.ACTION_GENERIC_WEATHER"

    /** The broadcast apps with permission get after each new forecast. */
    fun updatedAction(context: Context) = context.packageName + ".ACTION_WEATHER_UPDATED"

    /** The permission an app needs to read the forecasts. */
    fun readPermission(context: Context) = context.packageName + ".READ_WEATHER"

    /** Called after every new forecast is saved. */
    fun onNewForecast(context: Context, f: Forecast) {
        val s = Prefs(context).settings
        if (s.shareGadgetbridge) runCatching { sendToGadgetbridge(context, f) }
        if (s.shareApps) runCatching {
            context.sendBroadcast(Intent(updatedAction(context)), readPermission(context))
        }
    }

    /** The installed Gadgetbridge builds that take weather, by package name. */
    fun gadgetbridgePackages(context: Context): List<String> =
        context.packageManager.queryBroadcastReceivers(Intent(GADGETBRIDGE_ACTION), PackageManager.MATCH_ALL)
            .map { it.activityInfo.packageName }.distinct()

    fun sendToGadgetbridge(context: Context, f: Forecast) {
        val spec = gadgetbridgeSpec(f, conditionLabel(f.current.code, f.current.isDay))
        val one = json.encodeToString(GbWeather.serializer(), spec)
        val all = gzip("[$one]")
        // Android 14 and later only deliver to a named app, so send to each
        // Gadgetbridge build that is installed.
        gadgetbridgePackages(context).forEach { pkg ->
            context.sendBroadcast(
                Intent(GADGETBRIDGE_ACTION).setPackage(pkg)
                    .putExtra("WeatherGz", all)
                    .putExtra("WeatherJson", one)
                    .addFlags(Intent.FLAG_INCLUDE_STOPPED_PACKAGES),
            )
        }
    }

    private fun gzip(text: String): ByteArray {
        val out = ByteArrayOutputStream()
        GZIPOutputStream(out).use { it.write(text.toByteArray(Charsets.UTF_8)) }
        return out.toByteArray()
    }
}

// Gadgetbridge's WeatherSpec: temperatures in Kelvin, wind in km/h, times in
// seconds since 1970, conditions as OpenWeatherMap codes.

@Serializable
data class GbWeather(
    val timestamp: Int,
    val location: String,
    val currentTemp: Int,
    val currentConditionCode: Int,
    val currentCondition: String,
    val currentHumidity: Int,
    val todayMaxTemp: Int? = null,
    val todayMinTemp: Int? = null,
    val windSpeed: Float,
    val windDirection: Int,
    val uvIndex: Float? = null,
    val precipProbability: Int? = null,
    val feelsLikeTemp: Int,
    val sunRise: Int? = null,
    val sunSet: Int? = null,
    val forecasts: List<GbDay> = emptyList(),
    val hourly: List<GbHour> = emptyList(),
)

@Serializable
data class GbDay(
    val minTemp: Int,
    val maxTemp: Int,
    val conditionCode: Int,
    val precipProbability: Int,
    val uvIndex: Float,
    val sunRise: Int? = null,
    val sunSet: Int? = null,
)

@Serializable
data class GbHour(val timestamp: Int, val temp: Int, val conditionCode: Int, val precipProbability: Int)

fun kelvin(c: Double): Int = (c + 273.15).roundToInt()

/** Open-Meteo's weather codes (WMO) as the OpenWeatherMap codes Gadgetbridge expects. */
fun owmCode(wmo: Int): Int = when (wmo) {
    0 -> 800
    1 -> 801
    2 -> 802
    3 -> 804
    45, 48 -> 741
    51 -> 300
    53 -> 301
    55 -> 302
    56, 57 -> 511
    61 -> 500
    63 -> 501
    65 -> 502
    66, 67 -> 511
    71, 77 -> 600
    73 -> 601
    75 -> 602
    80 -> 520
    81 -> 521
    82 -> 522
    85 -> 620
    86 -> 622
    95 -> 211
    96, 99 -> 202
    else -> 804
}

fun gadgetbridgeSpec(f: Forecast, condition: String): GbWeather {
    val off = ZoneOffset.ofTotalSeconds(f.utcOffsetSeconds)
    fun secs(local: String) = runCatching { LocalDateTime.parse(local).toEpochSecond(off).toInt() }.getOrNull()
    val now = (f.fetchedAt / 1000).toInt()
    val today = f.days.firstOrNull()
    val c = f.current
    return GbWeather(
        timestamp = now,
        location = f.place.name,
        currentTemp = kelvin(c.tempC),
        currentConditionCode = owmCode(c.code),
        currentCondition = condition,
        currentHumidity = c.humidity,
        todayMaxTemp = today?.let { kelvin(it.maxC) },
        todayMinTemp = today?.let { kelvin(it.minC) },
        windSpeed = c.windKmh.toFloat(),
        windDirection = c.windDir,
        uvIndex = today?.uvMax?.toFloat(),
        precipProbability = today?.rainChance,
        feelsLikeTemp = kelvin(c.feelsC),
        sunRise = today?.let { secs(it.sunrise) },
        sunSet = today?.let { secs(it.sunset) },
        // Gadgetbridge's daily list starts tomorrow.
        forecasts = f.days.drop(1).map { d ->
            GbDay(kelvin(d.minC), kelvin(d.maxC), owmCode(d.code), d.rainChance, d.uvMax.toFloat(), secs(d.sunrise), secs(d.sunset))
        },
        hourly = f.hours.mapNotNull { h -> secs(h.time)?.let { t -> GbHour(t, kelvin(h.tempC), owmCode(h.code), h.rainChance) } }
            .filter { it.timestamp >= now - 3600 }.take(24),
    )
}
