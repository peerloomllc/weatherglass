package com.peerloom.weatherglass.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.net.URLEncoder

// Open-Meteo: free, no key, worldwide. Free tier is for non-commercial use
// and must be credited ("Weather data by Open-Meteo.com", CC BY 4.0).

val json = Json { ignoreUnknownKeys = true; explicitNulls = false }

object OpenMeteo {
    fun forecastUrl(lat: Double, lon: Double): String =
        "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon" +
            "&current=temperature_2m,apparent_temperature,relative_humidity_2m,is_day,weather_code,wind_speed_10m,wind_direction_10m" +
            "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,is_day" +
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max,sunshine_duration" +
            "&minutely_15=precipitation&forecast_days=10&forecast_hours=48&forecast_minutely_15=12&timezone=auto"

    fun parseForecast(body: String, place: Place, nowMillis: Long = System.currentTimeMillis()): Forecast {
        val r = json.decodeFromString(Resp.serializer(), body)
        val c = r.current
        val h = r.hourly
        val d = r.daily
        return Forecast(
            place = place,
            fetchedAt = nowMillis,
            utcOffsetSeconds = r.utcOffsetSeconds,
            current = Current(c.time, c.temp, c.feels, c.humidity, c.wind, c.windDir, c.code, c.isDay == 1),
            hours = h.time.indices.map { i ->
                Hour(h.time[i], h.temp[i] ?: 0.0, h.rainChance[i] ?: 0, h.rain[i] ?: 0.0, h.code[i] ?: 3, (h.isDay[i] ?: 1) == 1)
            },
            days = d.time.indices.map { i ->
                Day(d.time[i], d.code[i] ?: 3, d.max[i] ?: 0.0, d.min[i] ?: 0.0, d.rainChance[i] ?: 0, d.sunrise[i] ?: "", d.sunset[i] ?: "", d.uv[i] ?: 0.0,
                    (d.sun.getOrNull(i) ?: 0.0) / 3600)
            },
            quarters = r.minutely?.let { m -> m.time.indices.map { Quarter(m.time[it], m.rain[it] ?: 0.0) } } ?: emptyList(),
        )
    }

    fun fetch(place: Place): Forecast = parseForecast(httpGet(forecastUrl(place.lat, place.lon)), place)

    fun search(query: String): List<Place> {
        val q = URLEncoder.encode(query.trim(), "UTF-8")
        val body = httpGet("https://geocoding-api.open-meteo.com/v1/search?name=$q&count=8&format=json")
        return parseSearch(body)
    }

    fun parseSearch(body: String): List<Place> =
        json.decodeFromString(GeoResp.serializer(), body).results.orEmpty().map {
            Place(it.name, it.latitude, it.longitude, listOfNotNull(it.admin1, it.country).joinToString(", "))
        }

    @Serializable
    private class Resp(
        @SerialName("utc_offset_seconds") val utcOffsetSeconds: Int = 0,
        val current: Cur,
        val hourly: Hourly,
        val daily: Daily,
        @SerialName("minutely_15") val minutely: Minutely? = null,
    )

    @Serializable
    private class Cur(
        val time: String,
        @SerialName("temperature_2m") val temp: Double,
        @SerialName("apparent_temperature") val feels: Double,
        @SerialName("relative_humidity_2m") val humidity: Int,
        @SerialName("is_day") val isDay: Int,
        @SerialName("weather_code") val code: Int,
        @SerialName("wind_speed_10m") val wind: Double,
        @SerialName("wind_direction_10m") val windDir: Int,
    )

    @Serializable
    private class Hourly(
        val time: List<String>,
        @SerialName("temperature_2m") val temp: List<Double?>,
        @SerialName("precipitation_probability") val rainChance: List<Int?>,
        @SerialName("precipitation") val rain: List<Double?>,
        @SerialName("weather_code") val code: List<Int?>,
        @SerialName("is_day") val isDay: List<Int?>,
    )

    @Serializable
    private class Daily(
        val time: List<String>,
        @SerialName("weather_code") val code: List<Int?>,
        @SerialName("temperature_2m_max") val max: List<Double?>,
        @SerialName("temperature_2m_min") val min: List<Double?>,
        @SerialName("precipitation_probability_max") val rainChance: List<Int?>,
        val sunrise: List<String?>,
        val sunset: List<String?>,
        @SerialName("uv_index_max") val uv: List<Double?>,
        @SerialName("sunshine_duration") val sun: List<Double?> = emptyList(), // seconds
    )

    @Serializable
    private class Minutely(
        val time: List<String>,
        @SerialName("precipitation") val rain: List<Double?>,
    )

    @Serializable
    private class GeoResp(val results: List<GeoHit>? = null)

    @Serializable
    private class GeoHit(
        val name: String,
        val latitude: Double,
        val longitude: Double,
        val admin1: String? = null,
        val country: String? = null,
    )
}
