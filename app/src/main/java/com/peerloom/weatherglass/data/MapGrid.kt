package com.peerloom.weatherglass.data

import android.content.Context
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.builtins.ListSerializer
import java.io.File
import kotlin.math.cos

// The map screen's weather: rain for the next 12 hours and sunshine for the
// next 3 days on a square grid of points around a place, in one Open-Meteo
// request. Each point counts as one call against Open-Meteo's free limit of
// 10,000 a day, so the grid is only fetched when the map is opened and is
// kept for 30 minutes.

@Serializable
data class MapGrid(
    val lat0: Double,
    val lon0: Double,
    /** Half the height of the area, in degrees of latitude. */
    val span: Double,
    val n: Int,
    val fetchedAt: Long,
    /** Local hour labels (ISO) for [rain], e.g. 2026-11-26T14:00. */
    val hours: List<String>,
    /** mm of rain per hour: rain[hour][point], points row by row from the north-west. */
    val rain: List<List<Double>>,
    val days: List<String>,
    /** Hours of sunshine: sun[day][point]. */
    val sun: List<List<Double>>,
) {
    fun lat(row: Int) = lat0 + span - 2 * span * row / (n - 1)
    fun lon(col: Int) = lon0 - lonSpan + 2 * lonSpan * col / (n - 1)
    /** Half the width of the area in degrees of longitude, so the area is square on the ground. */
    val lonSpan get() = span / cos(Math.toRadians(lat0)).coerceAtLeast(0.2)
}

object MapWeather {
    const val N = 13 // 169 points
    const val SPAN = 2.0 // about 450 km across
    private const val MAX_AGE_MS = 30 * 60_000L

    fun points(lat0: Double, lon0: Double, n: Int = N, span: Double = SPAN): List<Pair<Double, Double>> {
        val g = MapGrid(lat0, lon0, span, n, 0, emptyList(), emptyList(), emptyList(), emptyList())
        return (0 until n).flatMap { r -> (0 until n).map { c -> g.lat(r) to g.lon(c) } }
    }

    fun url(pts: List<Pair<Double, Double>>): String =
        "https://api.open-meteo.com/v1/forecast?latitude=" + pts.joinToString(",") { "%.3f".format(it.first) } +
            "&longitude=" + pts.joinToString(",") { "%.3f".format(it.second) } +
            "&hourly=precipitation&daily=sunshine_duration&forecast_hours=12&forecast_days=3&timezone=auto"

    fun parse(body: String, lat0: Double, lon0: Double, nowMillis: Long, n: Int = N, span: Double = SPAN): MapGrid {
        val r = json.decodeFromString(ListSerializer(Point.serializer()), body)
        val first = r.first()
        return MapGrid(
            lat0, lon0, span, n, nowMillis,
            hours = first.hourly.time,
            rain = first.hourly.time.indices.map { h -> r.map { it.hourly.rain.getOrNull(h) ?: 0.0 } },
            days = first.daily.time,
            sun = first.daily.time.indices.map { d -> r.map { (it.daily.sun.getOrNull(d) ?: 0.0) / 3600 } },
        )
    }

    /** The grid around a place: saved if under 30 minutes old, otherwise downloaded. */
    fun load(context: Context, place: Place, nowMillis: Long = System.currentTimeMillis()): MapGrid {
        val file = File(context.cacheDir, "map.json")
        runCatching { json.decodeFromString(MapGrid.serializer(), file.readText()) }.getOrNull()?.let { g ->
            if (g.lat0 == place.lat && g.lon0 == place.lon && nowMillis - g.fetchedAt < MAX_AGE_MS) return g
        }
        val g = parse(httpGet(url(points(place.lat, place.lon))), place.lat, place.lon, nowMillis)
        runCatching { file.writeText(json.encodeToString(MapGrid.serializer(), g)) }
        return g
    }

    @Serializable
    private class Point(val hourly: Hourly, val daily: Daily)

    @Serializable
    private class Hourly(val time: List<String>, @SerialName("precipitation") val rain: List<Double?>)

    @Serializable
    private class Daily(val time: List<String>, @SerialName("sunshine_duration") val sun: List<Double?>)
}
