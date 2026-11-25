package com.peerloom.weatherglass.data

import kotlin.math.roundToInt

enum class TempUnit { F, C }
enum class WindUnit(val label: String) { MPH("mph"), KMH("km/h"), MS("m/s") }

fun temp(c: Double, unit: TempUnit): Int =
    if (unit == TempUnit.F) (c * 9 / 5 + 32).roundToInt() else c.roundToInt()

fun tempText(c: Double, unit: TempUnit): String = "${temp(c, unit)}°"

fun windText(kmh: Double, unit: WindUnit): String = when (unit) {
    WindUnit.MPH -> "${(kmh / 1.609344).roundToInt()} mph"
    WindUnit.KMH -> "${kmh.roundToInt()} km/h"
    WindUnit.MS -> "${(kmh / 3.6).roundToInt()} m/s"
}

fun rainText(mm: Double, unit: TempUnit): String =
    if (unit == TempUnit.F) String.format("%.2f in", mm / 25.4) else String.format("%.1f mm", mm)

private val COMPASS = listOf("N", "NE", "E", "SE", "S", "SW", "W", "NW")
fun compass(deg: Int): String = COMPASS[(((deg % 360) + 360) % 360 + 22) / 45 % 8]
