package com.peerloom.weatherglass.data

import java.time.Duration
import java.time.LocalDateTime

// The one-line "Rain starting in about 20 minutes" message, from Open-Meteo's
// 15-minute forecast. Returns null when nothing changes in the next two hours,
// so the line simply is not shown.

private const val WET_MM = 0.1 // per 15 minutes

fun rainTiming(quarters: List<Quarter>, now: LocalDateTime, snow: Boolean = false): String? {
    val ahead = quarters
        .map { parseLocal(it.time) to it.rainMm }
        .filter { (t, _) -> !t.isBefore(now.minusMinutes(14)) && t.isBefore(now.plusHours(2)) }
    if (ahead.isEmpty()) return null
    val word = if (snow) "Snow" else "Rain"
    val wetNow = ahead.first().second >= WET_MM
    val change = ahead.drop(1).firstOrNull { (_, mm) -> (mm >= WET_MM) != wetNow } ?: return null
    val mins = Duration.between(now, change.first).toMinutes().coerceAtLeast(5)
    val when_ = if (mins < 60) "in about ${roundTo5(mins)} minutes" else "in about ${if (mins < 90) "an hour" else "2 hours"}"
    return if (wetNow) "$word stopping $when_" else "$word starting $when_"
}

private fun roundTo5(m: Long) = (((m + 2) / 5) * 5).coerceAtLeast(5)
