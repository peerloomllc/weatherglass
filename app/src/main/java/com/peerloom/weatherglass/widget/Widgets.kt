package com.peerloom.weatherglass.widget

import android.content.Context
import android.content.res.Configuration
import android.util.TypedValue
import android.widget.RemoteViews
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.glance.ColorFilter
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.Image
import androidx.glance.ImageProvider
import androidx.glance.LocalSize
import androidx.glance.action.actionStartActivity
import androidx.glance.action.clickable
import androidx.glance.appwidget.AndroidRemoteViews
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetManager
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.SizeMode
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.provideContent
import androidx.glance.appwidget.state.updateAppWidgetState
import androidx.glance.background
import androidx.glance.currentState
import androidx.glance.layout.Alignment
import androidx.glance.layout.Box
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.layout.size
import androidx.glance.layout.width
import androidx.glance.text.FontFamily
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import com.peerloom.weatherglass.R
import com.peerloom.weatherglass.data.Cache
import com.peerloom.weatherglass.data.Forecast
import com.peerloom.weatherglass.data.Prefs
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.data.conditionLabel
import com.peerloom.weatherglass.data.dayLabel
import com.peerloom.weatherglass.data.hourLabel
import com.peerloom.weatherglass.data.parseLocal
import com.peerloom.weatherglass.data.placeNow
import com.peerloom.weatherglass.data.tempText
import com.peerloom.weatherglass.skin.Font
import com.peerloom.weatherglass.skin.Palette
import com.peerloom.weatherglass.skin.Skin
import com.peerloom.weatherglass.skin.Skins
import com.peerloom.weatherglass.skin.iconFor
import com.peerloom.weatherglass.ui.MainActivity

// Four widgets. Each shows a chosen set of parts (clock, date, place, high
// and low, rain chance, next hours, next days), picked on the widget's
// settings screen. Each kind has its own defaults. Parts that do not fit the
// widget's current size are left out, lowest first.
//
// Widgets read the saved forecast and never touch the network themselves.
// Tapping one opens the app.

enum class Part(val label: String) {
    CLOCK("Time"),
    DATE("Date"),
    PLACE("Place name"),
    HIGH_LOW("Today's high and low"),
    RAIN("Rain chance"),
    HOURS("Next hours"),
    DAYS("Next days"),
}

fun partKey(p: Part) = booleanPreferencesKey("part_${p.name}")

// A widget's content keeps running between updates, so it must not hold on
// to what it read at start. Each update bumps this number in the widget's
// own state, and the content reloads the saved forecast when it changes.
private val VERSION = longPreferencesKey("version")

object Widgets {
    val all: List<WeatherWidget> get() = listOf(SmallWidget(), MediumWidget(), LargeWidget(), ClockWidget())

    fun byReceiver(className: String?): WeatherWidget? = when (className) {
        SmallWidgetReceiver::class.java.name -> SmallWidget()
        MediumWidgetReceiver::class.java.name -> MediumWidget()
        LargeWidgetReceiver::class.java.name -> LargeWidget()
        ClockWidgetReceiver::class.java.name -> ClockWidget()
        else -> null
    }

    suspend fun updateAll(context: Context) {
        val mgr = GlanceAppWidgetManager(context)
        all.forEach { w ->
            runCatching { mgr.getGlanceIds(w.javaClass).forEach { id -> bump(context, w, id) } }
        }
    }

    suspend fun bump(context: Context, w: GlanceAppWidget, id: GlanceId) {
        updateAppWidgetState(context, id) { it[VERSION] = (it[VERSION] ?: 0L) + 1 }
        w.update(context, id)
    }
}

internal class WData(val forecast: Forecast?, val settings: Settings, val skin: Skin, val p: Palette)

private fun load(context: Context): WData {
    val prefs = Prefs(context)
    val s = prefs.settings
    val skin = Skins.byId(s.skin)
    val dark = (context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
    val f = prefs.selectedPlace()?.let { Cache(context).load(it) }
    return WData(f, s, skin, skin.palette(dark))
}

abstract class WeatherWidget : GlanceAppWidget() {
    abstract val defaults: Set<Part>
    override val sizeMode: SizeMode = SizeMode.Exact

    fun parts(state: Preferences): Set<Part> =
        Part.entries.filter { state[partKey(it)] ?: (it in defaults) }.toSet()

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        provideContent {
            val state = currentState<Preferences>()
            val version = state[VERSION] ?: 0L
            val d = remember(version) { load(context) }
            Frame(d) { Body(context, d, parts(state)) }
        }
    }
}

class SmallWidget : WeatherWidget() { override val defaults = setOf(Part.PLACE) }
class MediumWidget : WeatherWidget() { override val defaults = setOf(Part.PLACE, Part.HIGH_LOW, Part.RAIN, Part.HOURS) }
class LargeWidget : WeatherWidget() { override val defaults = setOf(Part.PLACE, Part.HIGH_LOW, Part.RAIN, Part.HOURS, Part.DAYS) }
class ClockWidget : WeatherWidget() { override val defaults = setOf(Part.CLOCK, Part.DATE, Part.PLACE, Part.HIGH_LOW) }

class SmallWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = SmallWidget() }
class MediumWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = MediumWidget() }
class LargeWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = LargeWidget() }
class ClockWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = ClockWidget() }

// Rough heights in dp, used to decide what fits.
private const val PAD = 28
private const val CLOCK_H = 52
private const val DATE_H = 20
private const val NOW_H = 50
private const val HOURS_H = 62
private const val DAY_H = 25

@Composable
private fun Body(context: Context, d: WData, parts: Set<Part>) {
    val size = LocalSize.current
    val f = d.forecast
    val clock = Part.CLOCK in parts
    val date = Part.DATE in parts
    if (size.height < 90.dp || size.width < 180.dp) return Compact(context, d, f, parts)

    var room = size.height.value.toInt() - PAD
    val showClock = (clock || date) && room >= NOW_H + CLOCK_H
    if (showClock) room -= (if (clock) CLOCK_H else 0) + (if (date) DATE_H else 0)
    room -= NOW_H
    val showHours = f != null && Part.HOURS in parts && room >= HOURS_H
    if (showHours) room -= HOURS_H + 8
    val dayCount = if (f != null && Part.DAYS in parts) (room / DAY_H).coerceIn(0, 6) else 0

    Column(GlanceModifier.fillMaxSize(), verticalAlignment = Alignment.CenterVertically) {
        if (showClock) {
            Clock(context, d, clock, date, if (size.width < 200.dp) 36 else 44)
            Spacer(GlanceModifier.height(6.dp))
        }
        if (f == null) {
            Txt(d, "Open Weatherglass to set a place", 13.sp, subtle = true)
            return@Column
        }
        NowRow(context, d, f, parts)
        if (showHours) {
            Spacer(GlanceModifier.height(8.dp))
            HoursRow(context, d, f, if (size.width < 200.dp) 3 else 5, Part.RAIN in parts)
        }
        if (dayCount > 0) {
            Spacer(GlanceModifier.height(6.dp))
            DaysRows(context, d, f, dayCount, Part.RAIN in parts)
        }
    }
}

// Short widgets: optional clock, then icon and temperature, with the place
// and high/low beside them, or under them when the widget is narrow.
@Composable
private fun Compact(context: Context, d: WData, f: Forecast?, parts: Set<Part>) {
    val narrow = LocalSize.current.width < 140.dp
    val sub = f?.let {
        listOfNotNull(
            it.days.firstOrNull()?.takeIf { Part.HIGH_LOW in parts }?.let { t -> "${tempText(t.maxC, d.settings.tempUnit)} / ${tempText(t.minC, d.settings.tempUnit)}" },
            it.place.name.takeIf { Part.PLACE in parts },
        ).joinToString("  ·  ")
    } ?: ""
    Row(GlanceModifier.fillMaxSize(), verticalAlignment = Alignment.CenterVertically) {
        if (Part.CLOCK in parts || Part.DATE in parts) {
            Clock(context, d, Part.CLOCK in parts, Part.DATE in parts, 30)
            Spacer(GlanceModifier.width(12.dp))
        }
        if (f == null) {
            Txt(d, "Open Weatherglass", 13.sp, subtle = true)
            return@Row
        }
        Column(GlanceModifier.defaultWeight()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(context, d, f.current.code, f.current.isDay, if (narrow) 26.dp else 36.dp)
                Spacer(GlanceModifier.width(if (narrow) 4.dp else 8.dp))
                Column {
                    Txt(d, tempText(f.current.tempC, d.settings.tempUnit), if (narrow) 22.sp else 26.sp)
                    if (!narrow && sub.isNotEmpty()) Txt(d, sub, 12.sp, subtle = true)
                }
            }
            if (narrow && sub.isNotEmpty()) Txt(d, sub, 11.sp, subtle = true)
        }
    }
}

@Composable
private fun Frame(d: WData, content: @Composable () -> Unit) {
    val small = LocalSize.current.let { it.width < 140.dp || it.height < 90.dp }
    Box(
        GlanceModifier.fillMaxSize().background(Color(d.p.bgTop)).cornerRadius(d.skin.corner.coerceAtLeast(4).dp)
            .padding(if (small) 8.dp else 14.dp).clickable(actionStartActivity<MainActivity>()),
        contentAlignment = Alignment.CenterStart,
    ) { content() }
}

@Composable
private fun Clock(context: Context, d: WData, time: Boolean, date: Boolean, timeSp: Int) {
    val layout = when (d.skin.font) {
        Font.SERIF -> R.layout.widget_clock_serif
        Font.MONO -> R.layout.widget_clock_mono
        Font.SANS -> R.layout.widget_clock_sans
    }
    val rv = RemoteViews(context.packageName, layout).apply {
        val pattern = if (d.settings.use24h) "HH:mm" else "h:mm"
        setCharSequence(R.id.clock_time, "setFormat12Hour", pattern)
        setCharSequence(R.id.clock_time, "setFormat24Hour", pattern)
        setTextColor(R.id.clock_time, d.p.text.toInt())
        setTextViewTextSize(R.id.clock_time, TypedValue.COMPLEX_UNIT_SP, timeSp.toFloat())
        setViewVisibility(R.id.clock_time, if (time) android.view.View.VISIBLE else android.view.View.GONE)
        setTextColor(R.id.clock_date, d.p.subtle.toInt())
        setTextViewTextSize(R.id.clock_date, TypedValue.COMPLEX_UNIT_SP, if (time) 14f else 18f)
        setViewVisibility(R.id.clock_date, if (date) android.view.View.VISIBLE else android.view.View.GONE)
    }
    // Without a set height the embedded clock takes all the room it is given.
    val h = (if (time) timeSp + 8 else 0) + (if (date) (if (time) 20 else 26) else 0)
    AndroidRemoteViews(rv, GlanceModifier.height(h.dp))
}

@Composable
private fun NowRow(context: Context, d: WData, f: Forecast, parts: Set<Part>) {
    val c = f.current
    val today = f.days.firstOrNull()
    Row(GlanceModifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(context, d, c.code, c.isDay, 44.dp)
        Spacer(GlanceModifier.width(10.dp))
        Txt(d, tempText(c.tempC, d.settings.tempUnit), 34.sp)
        Spacer(GlanceModifier.width(12.dp))
        Column(GlanceModifier.defaultWeight()) {
            Txt(d, label(d, conditionLabel(c.code, c.isDay)), 14.sp, bold = true)
            val sub = listOfNotNull(
                today?.takeIf { Part.HIGH_LOW in parts }?.let { "H ${tempText(it.maxC, d.settings.tempUnit)}  L ${tempText(it.minC, d.settings.tempUnit)}" },
                today?.takeIf { Part.RAIN in parts && it.rainChance >= 20 }?.let { "Rain ${it.rainChance}%" },
                f.place.name.takeIf { Part.PLACE in parts },
            ).joinToString("  ·  ")
            if (sub.isNotEmpty()) Txt(d, sub, 12.sp, subtle = true)
        }
    }
}

@Composable
private fun HoursRow(context: Context, d: WData, f: Forecast, n: Int, rain: Boolean) {
    val start = placeNow(f.utcOffsetSeconds).withMinute(0).withSecond(0)
    val hours = f.hours.filter { !parseLocal(it.time).isBefore(start) }.take(n)
    Row(GlanceModifier.fillMaxWidth()) {
        hours.forEach { h ->
            Column(GlanceModifier.defaultWeight(), horizontalAlignment = Alignment.CenterHorizontally) {
                Txt(d, if (h === hours.first()) "Now" else hourLabel(h.time, d.settings.use24h), 11.sp, subtle = true)
                Icon(context, d, h.code, h.isDay, 22.dp)
                Txt(d, tempText(h.tempC, d.settings.tempUnit), 13.sp, bold = true)
                if (rain) Txt(d, if (h.rainChance >= 20) "${h.rainChance}%" else " ", 10.sp, accent = true)
            }
        }
    }
}

@Composable
private fun DaysRows(context: Context, d: WData, f: Forecast, n: Int, rain: Boolean) {
    val today = placeNow(f.utcOffsetSeconds).toLocalDate()
    f.days.filter { !java.time.LocalDate.parse(it.date).isBefore(today) }.take(n).forEach { day ->
        Row(GlanceModifier.fillMaxWidth().padding(vertical = 2.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(GlanceModifier.defaultWeight()) { Txt(d, dayLabel(day.date, today), 14.sp) }
            if (rain) Txt(d, if (day.rainChance >= 20) "${day.rainChance}%  " else "", 11.sp, accent = true)
            Icon(context, d, day.code, true, 22.dp)
            Spacer(GlanceModifier.width(12.dp))
            Txt(d, tempText(day.minC, d.settings.tempUnit), 14.sp, subtle = true)
            Spacer(GlanceModifier.width(8.dp))
            Txt(d, tempText(day.maxC, d.settings.tempUnit), 14.sp, bold = true)
        }
    }
}

private fun label(d: WData, s: String) = if (d.skin.upperLabels) s.uppercase() else s

@Composable
private fun Icon(context: Context, d: WData, code: Int, isDay: Boolean, size: Dp) {
    val (res, isArt) = iconFor(context, d.skin, code, isDay)
    Image(
        ImageProvider(res), conditionLabel(code, isDay), GlanceModifier.size(size),
        colorFilter = if (isArt) null else ColorFilter.tint(ColorProvider(Color(d.p.icon))),
    )
}

@Composable
private fun Txt(d: WData, s: String, size: TextUnit, subtle: Boolean = false, bold: Boolean = false, accent: Boolean = false) = Text(
    s, maxLines = 1,
    style = TextStyle(
        color = ColorProvider(Color(if (accent) d.p.accent else if (subtle) d.p.subtle else d.p.text)),
        fontSize = size,
        fontWeight = if (bold) FontWeight.Medium else FontWeight.Normal,
        fontFamily = when (d.skin.font) { Font.SERIF -> FontFamily.Serif; Font.MONO -> FontFamily.Monospace; Font.SANS -> FontFamily.SansSerif },
    ),
)
