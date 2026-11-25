package com.peerloom.weatherglass.data

import java.time.Duration
import java.time.LocalDateTime

// The two alerts people can switch on themselves. Both only fire when the
// thing is about to happen, and at most once per event. Pure functions, so
// the background refresh calls them and the tests can too.

/** Tonight's low and when it happens, if it reaches [thresholdC]. */
data class Freeze(val lowC: Double, val at: LocalDateTime)

/**
 * Checked in the evening (4 pm to 10 pm, place time), once a day: the lowest
 * hourly temperature from now until 10 am tomorrow, if it is at or below
 * [thresholdC]. [lastSentDate] is the date it last fired (yyyy-mm-dd).
 */
fun freezeTonight(f: Forecast, now: LocalDateTime, thresholdC: Double, lastSentDate: String?): Freeze? {
    if (now.hour !in 16..21) return null
    if (lastSentDate == now.toLocalDate().toString()) return null
    val until = now.toLocalDate().plusDays(1).atTime(10, 0)
    val low = f.hours
        .map { parseLocal(it.time) to it.tempC }
        .filter { (t, _) -> !t.isBefore(now.withMinute(0)) && !t.isAfter(until) }
        .minByOrNull { it.second } ?: return null
    return if (low.second <= thresholdC) Freeze(low.second, low.first) else null
}

/** When rain (or snow) starts, if it is dry now and it starts within the hour. */
data class RainSoon(val minutes: Long, val snow: Boolean)

private const val WET_MM = 0.1 // per 15 minutes, same as the main screen line

/**
 * Rain starting within the next hour, from the 15-minute forecast. Quiet from
 * 10 pm to 7 am place time, and at most once every 2 hours ([lastSentMillis]).
 */
fun rainSoon(f: Forecast, now: LocalDateTime, nowMillis: Long, lastSentMillis: Long): RainSoon? {
    if (now.hour >= 22 || now.hour < 7) return null
    if (nowMillis - lastSentMillis < 2 * 60 * 60_000L) return null
    val ahead = f.quarters
        .map { parseLocal(it.time) to it.rainMm }
        .filter { (t, _) -> !t.isBefore(now.minusMinutes(14)) && !t.isAfter(now.plusMinutes(60)) }
    if (ahead.isEmpty() || ahead.first().second >= WET_MM) return null // already raining, or no data
    val start = ahead.drop(1).firstOrNull { it.second >= WET_MM }?.first ?: return null
    val hourCode = f.hours.firstOrNull { parseLocal(it.time).hour == start.hour && parseLocal(it.time).toLocalDate() == start.toLocalDate() }?.code
    val snow = hourCode?.let { conditionFor(it) == Condition.SNOW } ?: false
    return RainSoon(Duration.between(now, start).toMinutes().coerceAtLeast(5), snow)
}
