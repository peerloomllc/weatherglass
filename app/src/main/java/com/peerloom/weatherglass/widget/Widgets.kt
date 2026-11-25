package com.peerloom.weatherglass.widget

import android.content.Context
import android.content.res.Configuration
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.ColorFilter
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.Image
import androidx.glance.ImageProvider
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.action.actionStartActivity
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.provideContent
import androidx.glance.appwidget.updateAll
import androidx.glance.background
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

// Three widget sizes. All read the saved forecast for the selected place and
// never touch the network themselves. Tapping any of them opens the app.

object Widgets {
    suspend fun updateAll(context: Context) {
        runCatching { SmallWidget().updateAll(context) }
        runCatching { MediumWidget().updateAll(context) }
        runCatching { LargeWidget().updateAll(context) }
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

abstract class BaseWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val d = load(context)
        provideContent { Frame(context, d) { Body(context, d) } }
    }

    @Composable
    internal abstract fun Body(context: Context, d: WData)
}

class SmallWidget : BaseWidget() {
    @Composable
    override fun Body(context: Context, d: WData) {
        val f = d.forecast ?: return Empty(d)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(context, d, f.current.code, f.current.isDay, 40.dp)
            Spacer(GlanceModifier.width(8.dp))
            Column {
                Txt(d, tempText(f.current.tempC, d.settings.tempUnit), 30.sp)
                Txt(d, f.place.name, 12.sp, subtle = true)
            }
        }
    }
}

class MediumWidget : BaseWidget() {
    @Composable
    override fun Body(context: Context, d: WData) {
        val f = d.forecast ?: return Empty(d)
        Column(GlanceModifier.fillMaxSize(), verticalAlignment = Alignment.CenterVertically) {
            NowRow(context, d, f)
            Spacer(GlanceModifier.height(10.dp))
            HoursRow(context, d, f, 5)
        }
    }
}

class LargeWidget : BaseWidget() {
    @Composable
    override fun Body(context: Context, d: WData) {
        val f = d.forecast ?: return Empty(d)
        Column(GlanceModifier.fillMaxSize(), verticalAlignment = Alignment.CenterVertically) {
            NowRow(context, d, f)
            Spacer(GlanceModifier.height(10.dp))
            HoursRow(context, d, f, 5)
            Spacer(GlanceModifier.height(10.dp))
            val today = placeNow(f.utcOffsetSeconds).toLocalDate()
            f.days.filter { !java.time.LocalDate.parse(it.date).isBefore(today) }.take(4).forEach { day ->
                Row(GlanceModifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(GlanceModifier.defaultWeight()) { Txt(d, dayLabel(day.date, today), 14.sp) }
                    Icon(context, d, day.code, true, 22.dp)
                    Spacer(GlanceModifier.width(12.dp))
                    Txt(d, tempText(day.minC, d.settings.tempUnit), 14.sp, subtle = true)
                    Spacer(GlanceModifier.width(8.dp))
                    Txt(d, tempText(day.maxC, d.settings.tempUnit), 14.sp, bold = true)
                }
            }
        }
    }
}

class SmallWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = SmallWidget() }
class MediumWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = MediumWidget() }
class LargeWidgetReceiver : GlanceAppWidgetReceiver() { override val glanceAppWidget: GlanceAppWidget = LargeWidget() }

@Composable
private fun Frame(context: Context, d: WData, content: @Composable () -> Unit) {
    Box(
        GlanceModifier.fillMaxSize().background(Color(d.p.bgTop)).cornerRadius(d.skin.corner.coerceAtLeast(4).dp)
            .padding(14.dp).clickable(actionStartActivity<MainActivity>()),
        contentAlignment = Alignment.CenterStart,
    ) { content() }
}

@Composable
private fun Empty(d: WData) = Txt(d, "Open Weatherglass to set a place", 13.sp, subtle = true)

@Composable
private fun NowRow(context: Context, d: WData, f: Forecast) {
    val c = f.current
    val today = f.days.firstOrNull()
    Row(GlanceModifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(context, d, c.code, c.isDay, 44.dp)
        Spacer(GlanceModifier.width(10.dp))
        Txt(d, tempText(c.tempC, d.settings.tempUnit), 34.sp)
        Spacer(GlanceModifier.width(12.dp))
        Column(GlanceModifier.defaultWeight()) {
            Txt(d, label(d, conditionLabel(c.code, c.isDay)), 14.sp, bold = true)
            val hl = today?.let { "H ${tempText(it.maxC, d.settings.tempUnit)}  L ${tempText(it.minC, d.settings.tempUnit)}  ·  " } ?: ""
            Txt(d, hl + f.place.name, 12.sp, subtle = true)
        }
    }
}

@Composable
private fun HoursRow(context: Context, d: WData, f: Forecast, n: Int) {
    val start = placeNow(f.utcOffsetSeconds).withMinute(0).withSecond(0)
    val hours = f.hours.filter { !parseLocal(it.time).isBefore(start) }.take(n)
    Row(GlanceModifier.fillMaxWidth()) {
        hours.forEach { h ->
            Column(GlanceModifier.defaultWeight(), horizontalAlignment = Alignment.CenterHorizontally) {
                Txt(d, if (h === hours.first()) "Now" else hourLabel(h.time, d.settings.use24h), 11.sp, subtle = true)
                Icon(context, d, h.code, h.isDay, 22.dp)
                Txt(d, tempText(h.tempC, d.settings.tempUnit), 13.sp, bold = true)
            }
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
private fun Txt(d: WData, s: String, size: TextUnit, subtle: Boolean = false, bold: Boolean = false) = Text(
    s, maxLines = 1,
    style = TextStyle(
        color = ColorProvider(Color(if (subtle) d.p.subtle else d.p.text)),
        fontSize = size,
        fontWeight = if (bold) FontWeight.Medium else FontWeight.Normal,
        fontFamily = when (d.skin.font) { Font.SERIF -> FontFamily.Serif; Font.MONO -> FontFamily.Monospace; Font.SANS -> FontFamily.SansSerif },
    ),
)
