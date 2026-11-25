package com.peerloom.weatherglass.data

import kotlinx.serialization.Serializable

// Everything is stored in metric (°C, km/h, mm) and converted for display,
// so changing units never needs a new download.

@Serializable
data class Place(
    val name: String,
    val lat: Double,
    val lon: Double,
    val region: String = "",
    // The "My location" entry. Its lat/lon is the last fix we got while the
    // app was open. Background refreshes reuse it and never ask for location.
    val isCurrent: Boolean = false,
)

@Serializable
data class Current(
    val time: String,
    val tempC: Double,
    val feelsC: Double,
    val humidity: Int,
    val windKmh: Double,
    val windDir: Int,
    val code: Int,
    val isDay: Boolean,
)

@Serializable
data class Hour(
    val time: String, // local ISO, e.g. 2026-11-25T14:00
    val tempC: Double,
    val rainChance: Int,
    val rainMm: Double,
    val code: Int,
    val isDay: Boolean,
)

@Serializable
data class Day(
    val date: String, // 2026-11-25
    val code: Int,
    val maxC: Double,
    val minC: Double,
    val rainChance: Int,
    val sunrise: String,
    val sunset: String,
    val uvMax: Double,
)

@Serializable
data class Quarter(val time: String, val rainMm: Double)

@Serializable
data class Alert(
    val id: String,
    val event: String,
    val headline: String,
    val severity: String,
    val ends: String? = null,
    val description: String = "",
)

@Serializable
data class Forecast(
    val place: Place,
    val fetchedAt: Long, // epoch millis
    val utcOffsetSeconds: Int,
    val current: Current,
    val hours: List<Hour>,
    val days: List<Day>,
    val quarters: List<Quarter>,
    val alerts: List<Alert> = emptyList(),
)
