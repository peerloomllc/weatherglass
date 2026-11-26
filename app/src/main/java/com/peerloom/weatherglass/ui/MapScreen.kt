package com.peerloom.weatherglass.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.peerloom.weatherglass.data.MapGrid
import com.peerloom.weatherglass.data.MapWeather
import com.peerloom.weatherglass.data.Place
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.data.dayLabel
import com.peerloom.weatherglass.data.hourLabel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.LocalDate

// The map screen: rain for the next 12 hours or sunshine for the next 3 days,
// colored over built-in coastlines, borders and city names around the place.

private enum class Layer { RAIN, SUN }

@Composable
fun MapSheet(place: Place, settings: Settings, onDismiss: () -> Unit) = Sheet(onDismiss) {
    val context = LocalContext.current
    var grid by remember { mutableStateOf<MapGrid?>(null) }
    var failed by remember { mutableStateOf(false) }
    var layer by remember { mutableStateOf(Layer.RAIN) }
    var hour by remember { mutableIntStateOf(0) }
    var day by remember { mutableIntStateOf(0) }
    val base = remember { runCatching { Basemap.get(context) }.getOrNull() }
    LaunchedEffect(place) {
        failed = false
        grid = withContext(Dispatchers.IO) { runCatching { MapWeather.load(context, place) }.getOrNull() }
        failed = grid == null
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        T(look.label("Map"), 20.sp, weight = FontWeight.Medium)
        Choice(listOf("Rain" to Layer.RAIN, "Sunshine" to Layer.SUN), layer) { layer = it }
        Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp))).background(look.card)) {
            val g = grid
            when {
                g != null -> MapCanvas(g, base, layer, if (layer == Layer.RAIN) hour else day)
                failed -> Box(Modifier.fillMaxWidth().aspectRatio(1f), contentAlignment = Alignment.Center) {
                    T("Couldn't load the map. Check your connection.", 14.sp, look.subtle)
                }
                else -> Box(Modifier.fillMaxWidth().aspectRatio(1f), contentAlignment = Alignment.Center) {
                    T("Loading…", 14.sp, look.subtle)
                }
            }
        }
        val g = grid
        if (g != null) {
            if (layer == Layer.RAIN && g.hours.isNotEmpty()) {
                val i = hour.coerceIn(0, g.hours.lastIndex)
                T(if (i == 0) "Now" else hourLabel(g.hours[i], settings.use24h), 15.sp, weight = FontWeight.Medium)
                Slider(
                    value = i.toFloat(), onValueChange = { hour = it.toInt() },
                    valueRange = 0f..g.hours.lastIndex.toFloat(), steps = (g.hours.size - 2).coerceAtLeast(0),
                    colors = SliderDefaults.colors(thumbColor = look.accent, activeTrackColor = look.accent, inactiveTrackColor = look.subtle.copy(alpha = 0.3f)),
                )
                Legend(RAIN_STEPS.map { it.second to it.third }, "mm of rain per hour")
            } else if (layer == Layer.SUN && g.days.isNotEmpty()) {
                val today = LocalDate.now()
                Choice(g.days.mapIndexed { i, d -> dayLabel(d, today) to i }, day.coerceIn(0, g.days.lastIndex)) { day = it }
                Legend(SUN_STEPS.map { it.second to it.third }, "hours of sunshine")
            }
        }
        T("Forecast by Open-Meteo, not live radar. Map data: Natural Earth.", 12.sp, look.subtle)
    }
}

// Value it starts at, color, legend label.
private val RAIN_STEPS = listOf(
    Triple(0.1, Color(0xFF9BD3FF), "0.1"),
    Triple(0.5, Color(0xFF4EA8F5), "0.5"),
    Triple(2.0, Color(0xFF2364D9), "2"),
    Triple(5.0, Color(0xFF7B3FE4), "5"),
    Triple(10.0, Color(0xFFD23CC0), "10+"),
)
private val SUN_STEPS = listOf(
    Triple(0.0, Color(0xFF8D99AE), "0"),
    Triple(2.0, Color(0xFFE9D98B), "2"),
    Triple(4.0, Color(0xFFFFD23F), "4"),
    Triple(6.0, Color(0xFFFFA62B), "6"),
    Triple(8.0, Color(0xFFF46A1F), "8+"),
)

/**
 * The grid as a small picture, blended smoothly between points and between
 * the legend's colors, fading out below the first step. Drawn stretched over
 * the map.
 */
private fun smooth(values: List<Double>, n: Int, steps: List<Triple<Double, Color, String>>): androidx.compose.ui.graphics.ImageBitmap {
    val size = 128
    val bmp = android.graphics.Bitmap.createBitmap(size, size, android.graphics.Bitmap.Config.ARGB_8888)
    if (values.size < n * n) return bmp.asImageBitmapCompat()
    val px = IntArray(size * size)
    for (y in 0 until size) for (x in 0 until size) {
        val gx = x * (n - 1) / (size - 1).toDouble()
        val gy = y * (n - 1) / (size - 1).toDouble()
        val c0 = gx.toInt().coerceAtMost(n - 2)
        val r0 = gy.toInt().coerceAtMost(n - 2)
        val fx = gx - c0
        val fy = gy - r0
        fun at(r: Int, c: Int) = values[r * n + c]
        val v = at(r0, c0) * (1 - fx) * (1 - fy) + at(r0, c0 + 1) * fx * (1 - fy) +
            at(r0 + 1, c0) * (1 - fx) * fy + at(r0 + 1, c0 + 1) * fx * fy
        px[y * size + x] = shade(v, steps)
    }
    bmp.setPixels(px, 0, size, 0, 0, size, size)
    return bmp.asImageBitmapCompat()
}

private fun android.graphics.Bitmap.asImageBitmapCompat() = asImageBitmap()

private fun shade(v: Double, steps: List<Triple<Double, Color, String>>): Int {
    val first = steps.first()
    val alpha = 0.6f
    val c: Color = when {
        v < first.first * 0.5 -> return 0
        v < first.first -> first.second.copy(alpha = alpha * ((v - first.first * 0.5) / (first.first * 0.5)).toFloat())
        v >= steps.last().first -> steps.last().second.copy(alpha = alpha)
        else -> {
            val i = steps.indexOfLast { v >= it.first }
            val (a, ca, _) = steps[i]
            val (b, cb, _) = steps[i + 1]
            androidx.compose.ui.graphics.lerp(ca, cb, ((v - a) / (b - a)).toFloat()).copy(alpha = alpha)
        }
    }
    return c.toArgb()
}

@Composable
private fun Legend(items: List<Pair<Color, String>>, what: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        items.forEach { (c, label) ->
            Box(Modifier.size(12.dp).clip(RoundedCornerShape(3.dp)).background(c.copy(alpha = 0.8f)))
            Spacer(Modifier.width(4.dp))
            T(label, 12.sp, look.subtle)
            Spacer(Modifier.width(10.dp))
        }
    }
    T(what, 12.sp, look.subtle)
}

@Composable
private fun MapCanvas(g: MapGrid, base: Basemap?, layer: Layer, index: Int) {
    val measurer = rememberTextMeasurer()
    val line = look.text
    val subtle = look.subtle
    val accent = look.accent
    val halo = look.card
    val values = (if (layer == Layer.RAIN) g.rain else g.sun).getOrNull(index) ?: emptyList()
    val steps = if (layer == Layer.RAIN) RAIN_STEPS else SUN_STEPS
    val layerImage = remember(g, layer, index) { smooth(values, g.n, steps) }
    Canvas(Modifier.fillMaxWidth().aspectRatio(1f)) {
        val w = size.width
        // Degrees to pixels: the grid's points sit from edge to edge.
        fun px(lon: Float) = ((lon - g.lon0) / g.lonSpan + 1).toFloat() / 2 * w
        fun py(lat: Float) = ((g.lat0 - lat) / g.span + 1).toFloat() / 2 * w
        clipRect {
            drawImage(layerImage, dstSize = androidx.compose.ui.unit.IntSize(w.toInt(), w.toInt()))
            if (base != null) {
                outlines(base.states, ::px, ::py, subtle.copy(alpha = 0.45f), 0.8.dp.toPx(), PathEffect.dashPathEffect(floatArrayOf(6f, 6f)))
                outlines(base.borders, ::px, ::py, line.copy(alpha = 0.6f), 1.3.dp.toPx(), null)
                outlines(base.coast, ::px, ::py, line.copy(alpha = 0.75f), 1.4.dp.toPx(), null)
                outlines(base.lakes, ::px, ::py, line.copy(alpha = 0.55f), 1.dp.toPx(), null)
                // The biggest cities in view, spaced apart.
                val placed = mutableListOf(Offset(w / 2, w / 2))
                val gap = 56.dp.toPx()
                val style = TextStyle(color = line, fontSize = 11.sp, shadow = Shadow(halo, blurRadius = 6f))
                for (c in base.cities) {
                    if (placed.size > 9) break
                    val p = Offset(px(c.lon), py(c.lat))
                    if (p.x < 12 || p.y < 12 || p.x > w - 12 || p.y > w - 12) continue
                    if (placed.any { (it - p).getDistance() < gap }) continue
                    placed += p
                    drawCircle(line.copy(alpha = 0.8f), 2.5.dp.toPx(), p)
                    val t = measurer.measure(c.name, style)
                    val tx = (p.x - t.size.width / 2).coerceIn(2f, w - t.size.width - 2f)
                    drawText(t, topLeft = Offset(tx, p.y + 4.dp.toPx()))
                }
            }
            // The place itself.
            drawCircle(halo, 8.dp.toPx(), Offset(w / 2, w / 2))
            drawCircle(accent, 6.dp.toPx(), Offset(w / 2, w / 2))
        }
    }
}

private fun DrawScope.outlines(lines: List<FloatArray>, px: (Float) -> Float, py: (Float) -> Float, color: Color, width: Float, effect: PathEffect?) {
    val w = size.width
    val path = Path()
    for (l in lines) {
        var on = false
        var i = 0
        while (i < l.size) {
            val x = px(l[i])
            val y = py(l[i + 1])
            val inside = x > -w && x < 2 * w && y > -w && y < 2 * w
            if (inside && on) path.lineTo(x, y) else if (inside) { path.moveTo(x, y); on = true } else on = false
            i += 2
        }
    }
    drawPath(path, color, style = Stroke(width, pathEffect = effect))
}
