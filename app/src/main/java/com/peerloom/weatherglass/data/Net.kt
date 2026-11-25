package com.peerloom.weatherglass.data

import java.net.HttpURLConnection
import java.net.URL

// Plain HttpURLConnection keeps the app small. No HTTP library, no analytics.
// The User-Agent names the app only. The NWS asks for a contact, so we give
// the project page instead of anything about the user.
const val USER_AGENT = "Weatherglass/0.1 (github.com/peerloomllc/weatherglass)"

class HttpException(val code: Int) : Exception("HTTP $code")

fun httpGet(url: String, accept: String = "application/json"): String {
    val conn = URL(url).openConnection() as HttpURLConnection
    conn.connectTimeout = 10_000
    conn.readTimeout = 15_000
    conn.setRequestProperty("User-Agent", USER_AGENT)
    conn.setRequestProperty("Accept", accept)
    try {
        val code = conn.responseCode
        if (code !in 200..299) throw HttpException(code)
        return conn.inputStream.bufferedReader().use { it.readText() }
    } finally {
        conn.disconnect()
    }
}
