package com.peerloom.weatherglass.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

// Fetch, save and hand back. Alerts are fetched separately so a failed
// alerts call (or a place outside the US) never blocks the forecast.
class Repo(context: Context) {
    val prefs = Prefs(context)
    val cache = Cache(context)

    suspend fun refresh(place: Place): Forecast = withContext(Dispatchers.IO) {
        val f = OpenMeteo.fetch(place)
        val alerts = if (prefs.settings.alerts) runCatching { Nws.fetch(place.lat, place.lon) }.getOrDefault(emptyList()) else emptyList()
        f.copy(alerts = alerts).also { cache.save(it) }
    }

    // Skip the network when the saved forecast is younger than maxAgeMs.
    suspend fun refreshIfStale(place: Place, maxAgeMs: Long): Forecast? {
        val cached = cache.load(place)
        if (cached != null && System.currentTimeMillis() - cached.fetchedAt < maxAgeMs) return cached
        return runCatching { refresh(place) }.getOrElse { cached }
    }
}
