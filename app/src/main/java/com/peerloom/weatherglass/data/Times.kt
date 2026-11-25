package com.peerloom.weatherglass.data

import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.TextStyle
import java.util.Locale

// Open-Meteo is asked for times in the place's own time zone, so every time
// string is local to the place, not to the phone.

fun parseLocal(s: String): LocalDateTime = LocalDateTime.parse(s)

fun hourLabel(s: String, use24h: Boolean): String {
    val t = parseLocal(s)
    if (use24h) return t.format(DateTimeFormatter.ofPattern("HH:mm"))
    val h = t.hour % 12
    return "${if (h == 0) 12 else h}${if (t.hour < 12) "am" else "pm"}"
}

fun clockLabel(s: String, use24h: Boolean): String =
    parseLocal(s).format(DateTimeFormatter.ofPattern(if (use24h) "HH:mm" else "h:mm a", Locale.getDefault()))

fun dayLabel(date: String, today: LocalDate): String {
    val d = LocalDate.parse(date)
    return when (d) {
        today -> "Today"
        today.plusDays(1) -> "Tomorrow"
        else -> d.dayOfWeek.getDisplayName(TextStyle.SHORT, Locale.getDefault())
    }
}

// The place's local time right now.
fun placeNow(utcOffsetSeconds: Int, nowMillis: Long = System.currentTimeMillis()): LocalDateTime =
    LocalDateTime.ofEpochSecond(nowMillis / 1000 + utcOffsetSeconds, 0, java.time.ZoneOffset.UTC)
