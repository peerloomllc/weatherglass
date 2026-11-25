package com.peerloom.weatherglass.data

import android.content.Context
import kotlinx.serialization.builtins.ListSerializer
import java.util.Locale

data class Settings(
    val tempUnit: TempUnit,
    val windUnit: WindUnit,
    val use24h: Boolean,
    val skin: String,
    val alerts: Boolean,
)

// Small key-value settings plus the saved places list. One SharedPreferences
// file, read by the app, the widgets and the background refresh.
class Prefs(context: Context) {
    private val p = context.applicationContext.getSharedPreferences("weatherglass", Context.MODE_PRIVATE)

    private fun usLocale() = Locale.getDefault().country in setOf("US", "LR", "MM")

    var settings: Settings
        get() = Settings(
            tempUnit = p.getString("temp", null)?.let { TempUnit.valueOf(it) } ?: if (usLocale()) TempUnit.F else TempUnit.C,
            windUnit = p.getString("wind", null)?.let { WindUnit.valueOf(it) } ?: if (usLocale()) WindUnit.MPH else WindUnit.KMH,
            use24h = p.getBoolean("24h", !usLocale()),
            skin = p.getString("skin", "mono") ?: "mono",
            alerts = p.getBoolean("alerts", true),
        )
        set(s) {
            p.edit()
                .putString("temp", s.tempUnit.name)
                .putString("wind", s.windUnit.name)
                .putBoolean("24h", s.use24h)
                .putString("skin", s.skin)
                .putBoolean("alerts", s.alerts)
                .apply()
        }

    var places: List<Place>
        get() = p.getString("places", null)?.let {
            runCatching { json.decodeFromString(ListSerializer(Place.serializer()), it) }.getOrNull()
        } ?: emptyList()
        set(v) { p.edit().putString("places", json.encodeToString(ListSerializer(Place.serializer()), v)).apply() }

    var selected: Int
        get() = p.getInt("selected", 0)
        set(v) { p.edit().putInt("selected", v).apply() }

    var seenAlerts: Set<String>
        get() = p.getStringSet("seenAlerts", emptySet()) ?: emptySet()
        set(v) { p.edit().putStringSet("seenAlerts", v).apply() }

    fun selectedPlace(): Place? = places.getOrNull(selected) ?: places.firstOrNull()
}
