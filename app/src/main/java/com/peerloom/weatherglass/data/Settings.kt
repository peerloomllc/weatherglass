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
    val animate: Boolean = true,
    /** Your own alerts, both off until switched on. */
    val freezeAlert: Boolean = false,
    val freezeAtC: Double = 0.0,
    val rainSoonAlert: Boolean = false,
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
            animate = p.getBoolean("animate", true),
            freezeAlert = p.getBoolean("freezeAlert", false),
            freezeAtC = p.getFloat("freezeAtC", 0f).toDouble(),
            rainSoonAlert = p.getBoolean("rainSoonAlert", false),
        )
        set(s) {
            p.edit()
                .putString("temp", s.tempUnit.name)
                .putString("wind", s.windUnit.name)
                .putBoolean("24h", s.use24h)
                .putString("skin", s.skin)
                .putBoolean("alerts", s.alerts)
                .putBoolean("animate", s.animate)
                .putBoolean("freezeAlert", s.freezeAlert)
                .putFloat("freezeAtC", s.freezeAtC.toFloat())
                .putBoolean("rainSoonAlert", s.rainSoonAlert)
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

    /** Date (yyyy-mm-dd) the freeze alert last fired, so it fires once a night. */
    var lastFreezeDate: String?
        get() = p.getString("lastFreezeDate", null)
        set(v) { p.edit().putString("lastFreezeDate", v).apply() }

    /** When the rain-soon alert last fired (epoch millis). */
    var lastRainSoon: Long
        get() = p.getLong("lastRainSoon", 0L)
        set(v) { p.edit().putLong("lastRainSoon", v).apply() }

    /** When the app was first used (epoch millis); set on first read. */
    val firstUseAt: Long
        get() = p.getLong("firstUseAt", 0L).takeIf { it != 0L }
            ?: System.currentTimeMillis().also { p.edit().putLong("firstUseAt", it).apply() }

    /** Whether the one-time donation reminder has been shown. */
    var donateShown: Boolean
        get() = p.getBoolean("donateShown", false)
        set(v) { p.edit().putBoolean("donateShown", v).apply() }

    fun selectedPlace(): Place? = places.getOrNull(selected) ?: places.firstOrNull()
}

/** Days after first use before the one-time donation reminder, as in the other PeerLoom apps. */
const val DONATE_AFTER_MS = 14L * 24 * 60 * 60 * 1000

/** The donation reminder is due once, two weeks after first use, and never again. */
fun donationDue(firstUseAt: Long, shown: Boolean, now: Long): Boolean = !shown && now - firstUseAt >= DONATE_AFTER_MS
