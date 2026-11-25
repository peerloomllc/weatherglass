package com.peerloom.weatherglass.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.peerloom.weatherglass.R
import com.peerloom.weatherglass.data.Alert
import com.peerloom.weatherglass.data.Condition
import com.peerloom.weatherglass.data.Forecast
import com.peerloom.weatherglass.data.Place
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.data.clockLabel
import com.peerloom.weatherglass.data.compass
import com.peerloom.weatherglass.data.conditionFor
import com.peerloom.weatherglass.data.conditionLabel
import com.peerloom.weatherglass.data.dayLabel
import com.peerloom.weatherglass.data.hourLabel
import com.peerloom.weatherglass.data.parseLocal
import com.peerloom.weatherglass.data.placeNow
import com.peerloom.weatherglass.data.rainText
import com.peerloom.weatherglass.data.rainTiming
import com.peerloom.weatherglass.data.temp
import com.peerloom.weatherglass.data.tempText
import com.peerloom.weatherglass.data.windText
import com.peerloom.weatherglass.skin.iconFor
import kotlin.math.roundToInt

@Composable
fun T(
    text: String,
    size: TextUnit = 15.sp,
    color: Color = look.text,
    weight: FontWeight = FontWeight.Normal,
    modifier: Modifier = Modifier,
    maxLines: Int = Int.MAX_VALUE,
    align: TextAlign? = null,
) = Text(
    text, modifier = modifier, maxLines = maxLines, overflow = TextOverflow.Ellipsis,
    style = TextStyle(color = color, fontSize = size, fontWeight = weight, fontFamily = look.font, textAlign = align ?: TextAlign.Unspecified),
)

@Composable
fun WeatherIcon(code: Int, isDay: Boolean, size: Dp) {
    val (res, isArt) = iconFor(LocalContext.current, look.skin, code, isDay, size < look.skin.miniBelow.dp)
    Image(
        painterResource(res), contentDescription = conditionLabel(code, isDay), modifier = Modifier.size(size),
        colorFilter = if (isArt) null else ColorFilter.tint(look.icon),
    )
}

@Composable
fun SmallIcon(res: Int, desc: String, onClick: () -> Unit) {
    Box(Modifier.size(44.dp).clip(RoundedCornerShape(22.dp)).clickable(onClick = onClick), contentAlignment = Alignment.Center) {
        Image(painterResource(res), desc, Modifier.size(24.dp), colorFilter = ColorFilter.tint(look.text))
    }
}

@Composable
fun Card(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Box(
        modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp)).background(look.card).padding(16.dp),
    ) { content() }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WeatherScreen(
    state: UiState,
    onRefresh: () -> Unit,
    onSelect: (Int) -> Unit,
    onRemove: (Int) -> Unit,
    onAdd: (Place) -> Unit,
    onUseLocation: () -> Unit,
    onSearch: (String) -> Unit,
    onSettings: (Settings) -> Unit,
) {
    var showPlaces by remember { mutableStateOf(false) }
    var showSettings by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(look.bgTop, look.bgBottom)))) {
        if (state.places.isEmpty()) {
            Welcome(onUseLocation = onUseLocation, onPickCity = { showPlaces = true })
        } else {
            PullToRefreshBox(isRefreshing = state.refreshing, onRefresh = onRefresh, modifier = Modifier.fillMaxSize()) {
                Forecast(state, onPlaces = { showPlaces = true }, onSettings = { showSettings = true })
            }
        }
    }
    if (showPlaces) PlacesSheet(state, onDismiss = { showPlaces = false; onSearch("") }, onSelect = { onSelect(it); showPlaces = false },
        onRemove = onRemove, onAdd = { onAdd(it); showPlaces = false; onSearch("") }, onUseLocation = { onUseLocation(); showPlaces = false }, onSearch = onSearch)
    if (showSettings) SettingsSheet(state.settings, onDismiss = { showSettings = false }, onChange = onSettings)
}

@Composable
private fun Welcome(onUseLocation: () -> Unit, onPickCity: () -> Unit) {
    Column(
        Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(32.dp),
        verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        WeatherIcon(2, true, 96.dp)
        Spacer(Modifier.height(24.dp))
        T("Weatherglass", 32.sp, weight = FontWeight.Light)
        Spacer(Modifier.height(8.dp))
        T("Your local weather. No ads, no account.", 15.sp, look.subtle)
        Spacer(Modifier.height(40.dp))
        Button(look.label("Use my location"), primary = true, onClick = onUseLocation)
        Spacer(Modifier.height(12.dp))
        Button(look.label("Search for a city"), onClick = onPickCity)
    }
}

@Composable
fun Button(text: String, primary: Boolean = false, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Box(
        modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(24.dp)))
            .background(if (primary) look.accent else look.card).clickable(onClick = onClick).padding(vertical = 16.dp),
        contentAlignment = Alignment.Center,
    ) {
        T(text, 16.sp, if (primary) look.bgTop else look.text, FontWeight.Medium)
    }
}

@Composable
private fun Forecast(state: UiState, onPlaces: () -> Unit, onSettings: () -> Unit) {
    val s = state.settings
    val place = state.places.getOrNull(state.selected)
    val f = state.forecast
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 20.dp, end = 20.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth().statusBarsPadding().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Row(Modifier.weight(1f).clip(RoundedCornerShape(12.dp)).clickable(onClick = onPlaces).padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (place?.isCurrent == true) {
                        Image(painterResource(R.drawable.ic_location), null, Modifier.size(18.dp), colorFilter = ColorFilter.tint(look.text))
                        Spacer(Modifier.width(6.dp))
                    }
                    T(place?.name ?: "", 20.sp, weight = FontWeight.Medium, maxLines = 1)
                    Image(painterResource(R.drawable.ic_down), "Change place", Modifier.size(22.dp), colorFilter = ColorFilter.tint(look.subtle))
                }
                SmallIcon(R.drawable.ic_tune, "Settings", onSettings)
            }
        }
        if (f == null) {
            item {
                T(if (state.refreshing) "Getting the forecast..." else state.error ?: "Pull down to load the forecast.", 16.sp, look.subtle, modifier = Modifier.padding(top = 40.dp))
            }
            return@LazyColumn
        }
        val now = placeNow(f.utcOffsetSeconds)
        items(f.alerts) { AlertCard(it) }
        item { Now(f, s) }
        val snow = conditionFor(f.current.code) == Condition.SNOW
        rainTiming(f.quarters, now, snow)?.let { line -> item { Card { T(line, 16.sp, weight = FontWeight.Medium) } } }
        item { Hourly(f, s, now) }
        item { Daily(f, s, now.toLocalDate()) }
        item { Details(f, s) }
        item { Footer(f, state.error) }
    }
}

@Composable
private fun AlertCard(a: Alert) {
    var open by remember { mutableStateOf(false) }
    val severe = a.severity == "Extreme" || a.severity == "Severe"
    val p = look.p
    val ink = Color(if (severe) p.alertText else p.alertMildText)
    Box(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp))
            .background(Color(if (severe) p.alert else p.alertMild)).clickable { open = !open }.padding(16.dp),
    ) {
        Column {
            T(look.label(a.event), 16.sp, ink, FontWeight.Bold, Modifier.fillMaxWidth(), align = TextAlign.Center)
            Spacer(Modifier.height(8.dp))
            T(a.headline, 14.sp, ink, maxLines = if (open) Int.MAX_VALUE else 2)
            if (open && a.description.isNotBlank()) {
                Spacer(Modifier.height(8.dp))
                T(a.description, 14.sp, ink)
            }
        }
    }
}

@Composable
private fun Now(f: Forecast, s: Settings) {
    val c = f.current
    val today = f.days.firstOrNull()
    Column(Modifier.fillMaxWidth().padding(vertical = 8.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        WeatherIcon(c.code, c.isDay, 120.dp)
        T(tempText(c.tempC, s.tempUnit), 96.sp, weight = FontWeight.Light)
        T(look.label(conditionLabel(c.code, c.isDay)), 20.sp)
        Spacer(Modifier.height(4.dp))
        val hl = today?.let { "  ·  H ${tempText(it.maxC, s.tempUnit)}  L ${tempText(it.minC, s.tempUnit)}" } ?: ""
        T("Feels like ${tempText(c.feelsC, s.tempUnit)}$hl", 15.sp, look.subtle)
    }
}

@Composable
private fun Hourly(f: Forecast, s: Settings, now: java.time.LocalDateTime) {
    val start = now.withMinute(0).withSecond(0)
    val hours = f.hours.filter { !parseLocal(it.time).isBefore(start) }.take(48)
    Card {
        Column {
            T(look.label("Next 48 hours"), 13.sp, look.subtle)
            Spacer(Modifier.height(10.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                items(hours) { h ->
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        T(if (h === hours.first()) "Now" else hourLabel(h.time, s.use24h), 13.sp, look.subtle)
                        Spacer(Modifier.height(6.dp))
                        WeatherIcon(h.code, h.isDay, 30.dp)
                        Spacer(Modifier.height(6.dp))
                        T(tempText(h.tempC, s.tempUnit), 16.sp, weight = FontWeight.Medium)
                        T(if (h.rainChance >= 20) "${h.rainChance}%" else " ", 12.sp, look.accent)
                    }
                }
            }
        }
    }
}

@Composable
private fun Daily(f: Forecast, s: Settings, today: java.time.LocalDate) {
    val days = f.days.filter { !java.time.LocalDate.parse(it.date).isBefore(today) }
    if (days.isEmpty()) return
    val lo = days.minOf { temp(it.minC, s.tempUnit) }
    val hi = days.maxOf { temp(it.maxC, s.tempUnit) }
    Card {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            T(look.label("Next ${days.size} days"), 13.sp, look.subtle)
            days.forEach { d ->
                Row(verticalAlignment = Alignment.CenterVertically) {
                    T(dayLabel(d.date, today), 16.sp, modifier = Modifier.width(86.dp), maxLines = 1)
                    WeatherIcon(d.code, true, 28.dp)
                    T(if (d.rainChance >= 20) "${d.rainChance}%" else "", 12.sp, look.accent, modifier = Modifier.width(40.dp).padding(start = 6.dp))
                    T(tempText(d.minC, s.tempUnit), 15.sp, look.subtle, modifier = Modifier.width(40.dp))
                    RangeBar(lo, hi, temp(d.minC, s.tempUnit), temp(d.maxC, s.tempUnit), Modifier.weight(1f))
                    T(tempText(d.maxC, s.tempUnit), 15.sp, weight = FontWeight.Medium, modifier = Modifier.width(44.dp).padding(start = 8.dp))
                }
            }
        }
    }
}

@Composable
private fun RangeBar(lo: Int, hi: Int, min: Int, max: Int, modifier: Modifier) {
    val span = (hi - lo).coerceAtLeast(1).toFloat()
    BoxWithConstraints(modifier.height(6.dp).clip(RoundedCornerShape(3.dp)).background(look.subtle.copy(alpha = 0.25f))) {
        val w = maxWidth
        Box(
            Modifier.padding(start = w * ((min - lo) / span)).width((w * ((max - min) / span)).coerceAtLeast(6.dp)).height(6.dp)
                .clip(RoundedCornerShape(3.dp)).background(look.accent),
        )
    }
}

@Composable
private fun Details(f: Forecast, s: Settings) {
    val c = f.current
    val d = f.days.firstOrNull()
    val todayRain = f.hours.filter { d != null && it.time.startsWith(d.date) }.sumOf { it.rainMm }
    val cells = buildList {
        add("Wind" to "${windText(c.windKmh, s.windUnit)} ${compass(c.windDir)}")
        add("Humidity" to "${c.humidity}%")
        if (d != null) {
            add("UV index" to "${d.uvMax.roundToInt()} ${uvWord(d.uvMax)}")
            add("Rain today" to rainText(todayRain, s.tempUnit))
            if (d.sunrise.isNotEmpty()) add("Sunrise" to clockLabel(d.sunrise, s.use24h))
            if (d.sunset.isNotEmpty()) add("Sunset" to clockLabel(d.sunset, s.use24h))
        }
    }
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        cells.chunked(2).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                row.forEach { (k, v) ->
                    Card(Modifier.weight(1f)) {
                        Column {
                            T(look.label(k), 13.sp, look.subtle)
                            Spacer(Modifier.height(4.dp))
                            T(v, 18.sp, weight = FontWeight.Medium)
                        }
                    }
                }
                if (row.size == 1) Spacer(Modifier.weight(1f))
            }
        }
    }
}

private fun uvWord(uv: Double) = when {
    uv < 3 -> "Low"; uv < 6 -> "Moderate"; uv < 8 -> "High"; uv < 11 -> "Very high"; else -> "Extreme"
}

@Composable
private fun Footer(f: Forecast, error: String?) {
    val mins = ((System.currentTimeMillis() - f.fetchedAt) / 60_000).toInt()
    val ago = when {
        mins < 1 -> "just now"
        mins < 60 -> "$mins min ago"
        mins < 60 * 24 -> "${mins / 60} hr ago"
        else -> "${mins / (60 * 24)} days ago"
    }
    Column(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        if (error != null) T(error, 13.sp, look.accent)
        T("Updated $ago", 13.sp, look.subtle)
        T("Weather data by Open-Meteo.com", 12.sp, look.subtle)
        if (f.alerts.isNotEmpty()) T("Alerts from the US National Weather Service", 12.sp, look.subtle)
    }
}
