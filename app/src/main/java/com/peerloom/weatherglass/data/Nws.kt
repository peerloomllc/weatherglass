package com.peerloom.weatherglass.data

import kotlinx.serialization.Serializable

// US National Weather Service active alerts. Free, no key, US only. Outside
// the US the call fails and we show no alerts.

object Nws {
    fun alertsUrl(lat: Double, lon: Double) =
        "https://api.weather.gov/alerts/active?point=${"%.4f".format(lat)},${"%.4f".format(lon)}"

    // Rough box around the US states and Puerto Rico. Places outside it are
    // never sent to the NWS at all.
    fun covers(lat: Double, lon: Double) = lat in 17.0..72.0 && (lon in -180.0..-64.0)

    fun fetch(lat: Double, lon: Double): List<Alert> =
        if (!covers(lat, lon)) emptyList()
        else parse(httpGet(alertsUrl(lat, lon), accept = "application/geo+json"))

    fun parse(body: String): List<Alert> =
        json.decodeFromString(Resp.serializer(), body).features.map {
            val p = it.properties
            Alert(p.id, p.event, p.headline ?: p.event, p.severity ?: "Unknown", p.ends ?: p.expires, p.description ?: "")
        }.sortedBy { severityRank(it.severity) }

    private fun severityRank(s: String) = when (s) {
        "Extreme" -> 0; "Severe" -> 1; "Moderate" -> 2; "Minor" -> 3; else -> 4
    }

    @Serializable private class Resp(val features: List<Feature> = emptyList())
    @Serializable private class Feature(val properties: Props)
    @Serializable private class Props(
        val id: String,
        val event: String,
        val headline: String? = null,
        val severity: String? = null,
        val ends: String? = null,
        val expires: String? = null,
        val description: String? = null,
    )
}

/** Groups of NWS alerts, each with its own notification switch. */
enum class AlertKind(val label: String) {
    TORNADO("Tornado"),
    TROPICAL("Hurricane & tropical"),
    THUNDER("Thunderstorm"),
    FLOOD("Flood"),
    WINTER("Winter & cold"),
    HEAT("Heat"),
    WIND_FIRE("Wind & fire"),
    OTHER("Other"),
}

/** Sorts an NWS event name such as "Tornado Warning" into its group. Order matters: "Wind Chill" is winter, not wind. */
fun alertKind(event: String): AlertKind {
    val e = event.lowercase()
    fun has(vararg w: String) = w.any { it in e }
    return when {
        has("tornado") -> AlertKind.TORNADO
        has("hurricane", "tropical", "typhoon", "storm surge", "extreme wind") -> AlertKind.TROPICAL
        has("thunderstorm") -> AlertKind.THUNDER
        has("flood", "hydrologic") -> AlertKind.FLOOD
        has("winter", "blizzard", "ice storm", "snow", "sleet", "freez", "frost", "cold", "wind chill") -> AlertKind.WINTER
        has("heat") -> AlertKind.HEAT
        has("wind", "fire", "red flag", "dust", "smoke") -> AlertKind.WIND_FIRE
        else -> AlertKind.OTHER
    }
}
