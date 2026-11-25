package com.peerloom.weatherglass.data

// The ten weather types every skin draws. Open-Meteo reports WMO weather
// codes, which fold down into these.
enum class Condition(val label: String) {
    CLEAR("Clear"),
    PARTLY_CLOUDY("Partly cloudy"),
    CLOUDY("Cloudy"),
    FOG("Fog"),
    DRIZZLE("Drizzle"),
    RAIN("Rain"),
    SLEET("Freezing rain"),
    SNOW("Snow"),
    THUNDER("Thunderstorm"),
}

fun conditionFor(code: Int): Condition = when (code) {
    0, 1 -> Condition.CLEAR
    2 -> Condition.PARTLY_CLOUDY
    3 -> Condition.CLOUDY
    45, 48 -> Condition.FOG
    51, 53, 55 -> Condition.DRIZZLE
    56, 57, 66, 67 -> Condition.SLEET
    61, 63, 65, 80, 81, 82 -> Condition.RAIN
    71, 73, 75, 77, 85, 86 -> Condition.SNOW
    95, 96, 99 -> Condition.THUNDER
    else -> Condition.CLOUDY
}

// "Clear" reads oddly at night, so the text changes with the time of day.
fun conditionLabel(code: Int, isDay: Boolean): String {
    val c = conditionFor(code)
    return when {
        c == Condition.CLEAR && code == 1 -> if (isDay) "Mostly sunny" else "Mostly clear"
        c == Condition.CLEAR -> if (isDay) "Sunny" else "Clear"
        else -> c.label
    }
}
