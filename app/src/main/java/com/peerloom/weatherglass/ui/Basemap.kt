package com.peerloom.weatherglass.ui

import android.content.Context
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * The map's built-in outlines and city names, from assets/basemap.bin
 * (Natural Earth, public domain; built by tools/basemap.py). Loaded once.
 * Each line is lon, lat pairs.
 */
class Basemap(val coast: List<FloatArray>, val borders: List<FloatArray>, val states: List<FloatArray>, val lakes: List<FloatArray>, val cities: List<City>) {
    class City(val lon: Float, val lat: Float, val pop: Int, val name: String)

    companion object {
        @Volatile private var loaded: Basemap? = null

        fun get(context: Context): Basemap = loaded ?: synchronized(this) {
            loaded ?: read(context.assets.open("basemap.bin").use { it.readBytes() }).also { loaded = it }
        }

        fun read(bytes: ByteArray): Basemap {
            val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
            check(String(bytes, 0, 4) == "WGM1")
            b.position(4)
            fun layer(): List<FloatArray> = List(b.int) {
                val n = b.short.toInt() and 0xFFFF
                FloatArray(n * 2) { b.float }
            }
            val coast = layer()
            val borders = layer()
            val states = layer()
            val lakes = layer()
            val cities = List(b.int) {
                val lon = b.float
                val lat = b.float
                val pop = b.int
                val name = ByteArray(b.get().toInt() and 0xFF).also { b.get(it) }
                City(lon, lat, pop, String(name, Charsets.UTF_8))
            }
            return Basemap(coast, borders, states, lakes, cities)
        }
    }
}
