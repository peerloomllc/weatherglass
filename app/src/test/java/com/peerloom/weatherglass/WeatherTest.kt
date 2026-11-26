package com.peerloom.weatherglass

import com.peerloom.weatherglass.data.Condition
import java.time.LocalDate
import com.peerloom.weatherglass.data.Nws
import com.peerloom.weatherglass.data.AlertKind
import com.peerloom.weatherglass.data.alertKind
import com.peerloom.weatherglass.data.OpenMeteo
import com.peerloom.weatherglass.data.Place
import com.peerloom.weatherglass.data.Quarter
import com.peerloom.weatherglass.data.TempUnit
import com.peerloom.weatherglass.data.WindUnit
import com.peerloom.weatherglass.data.compass
import com.peerloom.weatherglass.data.conditionFor
import com.peerloom.weatherglass.data.conditionLabel
import com.peerloom.weatherglass.data.hourLabel
import com.peerloom.weatherglass.data.rainTiming
import com.peerloom.weatherglass.data.temp
import com.peerloom.weatherglass.data.windText
import com.peerloom.weatherglass.data.Current
import com.peerloom.weatherglass.data.Forecast
import com.peerloom.weatherglass.data.Hour
import com.peerloom.weatherglass.data.Day
import com.peerloom.weatherglass.data.freezeTonight
import com.peerloom.weatherglass.data.rainSoon
import com.peerloom.weatherglass.data.donationDue
import com.peerloom.weatherglass.skin.Skins
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDateTime

class WeatherTest {
    private fun res(name: String) = javaClass.classLoader!!.getResource(name)!!.readText()

    @Test fun weatherCodes() {
        assertEquals(Condition.CLEAR, conditionFor(0))
        assertEquals(Condition.PARTLY_CLOUDY, conditionFor(2))
        assertEquals(Condition.FOG, conditionFor(48))
        assertEquals(Condition.RAIN, conditionFor(81))
        assertEquals(Condition.SLEET, conditionFor(66))
        assertEquals(Condition.SNOW, conditionFor(86))
        assertEquals(Condition.THUNDER, conditionFor(99))
        assertEquals("Clear", conditionLabel(0, false))
        assertEquals("Sunny", conditionLabel(0, true))
    }

    @Test fun units() {
        assertEquals(32, temp(0.0, TempUnit.F))
        assertEquals(72, temp(22.2, TempUnit.F))
        assertEquals(-4, temp(-4.4, TempUnit.C))
        assertEquals("10 mph", windText(16.1, WindUnit.MPH))
        assertEquals("5 m/s", windText(18.0, WindUnit.MS))
        assertEquals("N", compass(350))
        assertEquals("SW", compass(225))
        assertEquals("3pm", hourLabel("2026-11-25T15:00", false))
        assertEquals("12am", hourLabel("2026-11-25T00:00", false))
        assertEquals("15:00", hourLabel("2026-11-25T15:00", true))
    }

    private fun q(vararg mm: Double) = mm.mapIndexed { i, v ->
        Quarter(LocalDateTime.of(2026, 11, 25, 12, 0).plusMinutes(15L * i).toString(), v)
    }

    @Test fun alertKinds() {
        mapOf(
            "Tornado Warning" to AlertKind.TORNADO, "Tornado Watch" to AlertKind.TORNADO,
            "Hurricane Warning" to AlertKind.TROPICAL, "Tropical Storm Watch" to AlertKind.TROPICAL,
            "Storm Surge Warning" to AlertKind.TROPICAL, "Extreme Wind Warning" to AlertKind.TROPICAL,
            "Severe Thunderstorm Warning" to AlertKind.THUNDER,
            "Flash Flood Warning" to AlertKind.FLOOD, "Coastal Flood Advisory" to AlertKind.FLOOD,
            "Winter Storm Warning" to AlertKind.WINTER, "Freeze Warning" to AlertKind.WINTER,
            "Wind Chill Advisory" to AlertKind.WINTER, "Extreme Cold Warning" to AlertKind.WINTER,
            "Excessive Heat Warning" to AlertKind.HEAT,
            "High Wind Warning" to AlertKind.WIND_FIRE, "Red Flag Warning" to AlertKind.WIND_FIRE,
            "Dense Fog Advisory" to AlertKind.OTHER, "Air Quality Alert" to AlertKind.OTHER,
        ).forEach { (event, kind) -> assertEquals(event, kind, alertKind(event)) }
    }

    @Test fun rainTimingLine() {
        val now = LocalDateTime.of(2026, 11, 25, 12, 5)
        assertEquals("Rain starting in about 25 minutes", rainTiming(q(0.0, 0.0, 0.4, 0.6), now))
        assertEquals("Rain stopping in about 10 minutes", rainTiming(q(0.5, 0.0, 0.0), now))
        assertEquals("Snow starting in about 25 minutes", rainTiming(q(0.0, 0.0, 0.4), now, snow = true))
        assertNull(rainTiming(q(0.0, 0.0, 0.0, 0.0), now))
        assertNull(rainTiming(q(0.3, 0.3, 0.3), now))
        assertNull(rainTiming(emptyList(), now))
    }

    @Test fun parsesForecast() {
        val f = OpenMeteo.parseForecast(res("forecast.json"), Place("Berlin", 52.52, 13.41), nowMillis = 1L)
        assertEquals(3600, f.utcOffsetSeconds)
        assertEquals(48, f.hours.size)
        assertEquals(10, f.days.size)
        assertEquals(12, f.quarters.size)
        assertTrue(f.days.all { it.maxC >= it.minC })
        assertTrue(f.current.humidity in 0..100)
        assertEquals(7.5, f.days[0].sunHours, 0.001) // 27000 seconds
        assertEquals(0.0, f.days[1].sunHours, 0.001)
    }

    @Test fun sunHoursRoundToHalfHours() {
        assertEquals("7.5h", com.peerloom.weatherglass.ui.sunHoursShort(7.4))
        assertEquals("8h", com.peerloom.weatherglass.ui.sunHoursShort(7.9))
        assertEquals("10 h 38 min", com.peerloom.weatherglass.ui.hoursMinutes(10.0 + 38 / 60.0))
    }

    @Test fun parsesSearch() {
        val r = OpenMeteo.parseSearch(res("search.json"))
        assertEquals("Denver", r.first().name)
        assertTrue(r.first().region.contains("United States"))
        assertTrue(OpenMeteo.parseSearch("""{"generationtime_ms":0.1}""").isEmpty())
    }

    @Test fun parsesAlerts() {
        val a = Nws.parse(res("alerts.json"))
        assertTrue(a.isNotEmpty())
        assertTrue(a.all { it.id.isNotEmpty() && it.event.isNotEmpty() })
        assertTrue(Nws.parse("""{"features":[]}""").isEmpty())
    }

    @Test fun alertsOnlyAskedForUsPlaces() {
        assertTrue(Nws.covers(39.74, -104.98)) // Denver
        assertTrue(Nws.covers(61.2, -149.9)) // Anchorage
        assertTrue(Nws.covers(21.3, -157.9)) // Honolulu
        assertTrue(Nws.covers(18.47, -66.1)) // San Juan
        assertFalse(Nws.covers(48.86, 2.35)) // Paris
        assertFalse(Nws.covers(-33.9, 151.2)) // Sydney
    }

    @Test
    fun everySkinIsInExactlyOneGroup() {
        val grouped = Skins.groups.flatMap { it.second }
        assertEquals(Skins.all.size, grouped.size)
        assertEquals(Skins.all.map { it.id }.toSet(), grouped.map { it.id }.toSet())
    }

    private fun forecast(hours: List<Pair<String, Double>>, quarters: List<Pair<String, Double>> = emptyList()) = Forecast(
        place = Place("Testville", 0.0, 0.0), fetchedAt = 0, utcOffsetSeconds = 0,
        current = Current("2026-11-25T18:00", 5.0, 5.0, 50, 5.0, 0, 3, false),
        hours = hours.map { (t, c) -> Hour(t, c, 0, 0.0, 3, false) },
        days = emptyList(),
        quarters = quarters.map { (t, mm) -> Quarter(t, mm) },
    )

    @Test
    fun freezeFiresInTheEveningOncePerNight() {
        val f = forecast(listOf("2026-11-25T18:00" to 4.0, "2026-11-26T03:00" to -1.5, "2026-11-26T05:00" to -2.0, "2026-11-26T12:00" to -9.0))
        val evening = LocalDateTime.parse("2026-11-25T18:20")
        val fr = freezeTonight(f, evening, 0.0, null)!!
        assertEquals(-2.0, fr.lowC, 0.01) // the noon -9 is after 10 am, so not "tonight"
        assertEquals(5, fr.at.hour)
        assertNull(freezeTonight(f, evening, 0.0, "2026-11-25")) // already sent today
        assertNull(freezeTonight(f, LocalDateTime.parse("2026-11-25T11:00"), 0.0, null)) // not evening
        assertNull(freezeTonight(f, evening, -5.0, null)) // not cold enough
    }

    @Test
    fun rainSoonOnlyWhenDryAndStartingWithinTheHour() {
        val now = LocalDateTime.parse("2026-11-25T14:00")
        val ms = 10_000_000_000L
        val q = listOf("2026-11-25T14:00" to 0.0, "2026-11-25T14:15" to 0.0, "2026-11-25T14:30" to 0.4, "2026-11-25T14:45" to 0.8)
        val f = forecast(listOf("2026-11-25T14:00" to 10.0), q)
        assertEquals(30L, rainSoon(f, now, ms, 0L)!!.minutes)
        assertNull(rainSoon(f, now, ms, ms - 30 * 60_000L)) // sent half an hour ago
        assertNull(rainSoon(f, LocalDateTime.parse("2026-11-25T23:00"), ms, 0L)) // quiet hours
        val wet = forecast(emptyList(), listOf("2026-11-25T14:00" to 0.5, "2026-11-25T14:15" to 0.5))
        assertNull(rainSoon(wet, now, ms, 0L)) // already raining
        val later = forecast(emptyList(), listOf("2026-11-25T14:00" to 0.0, "2026-11-25T15:30" to 0.5))
        assertNull(rainSoon(later, now, ms, 0L)) // more than an hour away
    }

    @Test
    fun donationReminderOnceAfterTwoWeeks() {
        val day = 24 * 60 * 60 * 1000L
        assertFalse(donationDue(0L, false, 13 * day))
        assertTrue(donationDue(0L, false, 14 * day))
        assertFalse(donationDue(0L, true, 30 * day)) // already shown: never again
    }

    @Test
    fun dailySkinGoesThroughEverySkinWithoutRepeatsInARow() {
        val n = Skins.all.size
        val start = LocalDate.ofEpochDay(n * 600L) // the first day of a round
        val days = (0L until 10L * n).map { Skins.daily(start.plusDays(it)) }
        days.zipWithNext().forEach { (a, b) -> assertTrue(a.id != b.id) }
        // Each round of n days shows every skin once.
        days.chunked(n).forEach { round -> assertEquals(n, round.toSet().size) }
        assertEquals(Skins.daily(start), Skins.byId(Skins.DAILY, start))
        assertEquals(Skins.daily(start), Skins.daily(start)) // the same all day
    }

    @Test
    fun gadgetbridgeSpecUsesKelvinSecondsAndOwmCodes() {
        val f = Forecast(
            place = Place("Here", 1.0, 2.0),
            fetchedAt = 1_795_701_600_000L, // 2026-11-26T14:00Z
            utcOffsetSeconds = -18000,
            current = Current("2026-11-26T09:00", 20.0, 21.0, 70, 12.5, 90, 61, true),
            hours = listOf(
                Hour("2026-11-26T07:00", 19.0, 10, 0.0, 3, true), // more than an hour ago: dropped
                Hour("2026-11-26T10:00", 21.0, 40, 0.2, 61, true),
            ),
            days = listOf(
                Day("2026-11-26", 61, 25.0, 15.0, 60, "2026-11-26T06:52", "2026-11-26T17:30", 6.0),
                Day("2026-11-27", 0, 26.0, 16.0, 0, "2026-11-27T06:53", "2026-11-27T17:30", 7.0),
            ),
            quarters = emptyList(),
        )
        val g = com.peerloom.weatherglass.data.gadgetbridgeSpec(f, "Rain")
        assertEquals(1_795_701_600, g.timestamp)
        assertEquals(293, g.currentTemp)
        assertEquals(500, g.currentConditionCode)
        assertEquals(298, g.todayMaxTemp)
        assertEquals(1_795_693_920, g.sunRise) // 06:52 at UTC-5 is 11:52Z
        assertEquals(1, g.forecasts.size) // starts tomorrow
        assertEquals(800, g.forecasts[0].conditionCode)
        assertEquals(listOf(1_795_705_200), g.hourly.map { it.timestamp }) // 10:00 local = 15:00Z
    }
}
