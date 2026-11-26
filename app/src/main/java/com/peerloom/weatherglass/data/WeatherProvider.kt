package com.peerloom.weatherglass.data

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri

/**
 * Lets apps the person allows read the saved forecasts. Android checks the
 * READ_WEATHER permission before any query reaches this class (see the
 * manifest), and it returns nothing while "Other apps" is off in Settings.
 *
 * content://<package>.weather/forecast gives one row per saved place that
 * has a forecast. The format is in docs/SHARING.md.
 */
class WeatherProvider : ContentProvider() {
    override fun onCreate() = true

    override fun query(uri: Uri, projection: Array<out String>?, selection: String?, args: Array<out String>?, sort: String?): Cursor {
        val out = MatrixCursor(COLUMNS)
        val ctx = context ?: return out
        if (uri.pathSegments.firstOrNull() != "forecast") return out
        val prefs = Prefs(ctx)
        if (!prefs.settings.shareApps) return out
        val cache = Cache(ctx)
        val selected = prefs.selectedPlace()
        prefs.places.forEach { p ->
            val f = cache.load(p) ?: return@forEach
            out.addRow(
                arrayOf<Any>(
                    p.name, p.lat, p.lon, if (p.isCurrent) 1 else 0, if (p == selected) 1 else 0, f.fetchedAt,
                    json.encodeToString(Forecast.serializer(), f),
                ),
            )
        }
        return out
    }

    override fun getType(uri: Uri) = "vnd.android.cursor.dir/vnd.weatherglass.forecast"
    override fun insert(uri: Uri, values: ContentValues?): Uri? = null
    override fun delete(uri: Uri, selection: String?, args: Array<out String>?) = 0
    override fun update(uri: Uri, values: ContentValues?, selection: String?, args: Array<out String>?) = 0

    companion object {
        val COLUMNS = arrayOf("place", "lat", "lon", "is_current", "selected", "fetched_at", "json")
    }
}
