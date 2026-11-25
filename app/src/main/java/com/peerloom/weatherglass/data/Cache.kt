package com.peerloom.weatherglass.data

import android.content.Context
import java.io.File

// The last forecast for each place, saved as JSON so the app and widgets can
// show something the moment they open, before any network call.
class Cache(context: Context) {
    private val dir = File(context.applicationContext.filesDir, "forecasts").apply { mkdirs() }

    private fun file(place: Place) =
        File(dir, if (place.isCurrent) "current.json" else "%.3f_%.3f.json".format(place.lat, place.lon))

    fun load(place: Place): Forecast? = runCatching {
        json.decodeFromString(Forecast.serializer(), file(place).readText())
    }.getOrNull()

    fun save(f: Forecast) {
        val tmp = File(dir, "tmp.json")
        tmp.writeText(json.encodeToString(Forecast.serializer(), f))
        tmp.renameTo(file(f.place))
    }

    fun drop(place: Place) { file(place).delete() }
}
