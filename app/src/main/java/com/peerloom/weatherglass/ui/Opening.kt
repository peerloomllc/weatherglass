package com.peerloom.weatherglass.ui

import android.content.Context
import android.graphics.ImageDecoder
import android.graphics.drawable.Animatable2
import android.graphics.drawable.AnimatedImageDrawable
import android.graphics.drawable.Drawable
import android.provider.Settings as SystemSettings
import android.widget.ImageView
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathMeasure
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.viewinterop.AndroidView
import com.peerloom.weatherglass.skin.clipFor
import com.peerloom.weatherglass.skin.iconFor
import org.xmlpull.v1.XmlPullParser

/** How long the line icons take to draw themselves, in milliseconds. */
const val DRAW_MS = 1400

/**
 * The big weather icon, animated once when the app opens, in the skin's own
 * way. Skins with opening clips (res/raw/clip_<skin>_<weather>_<day|night>.webp,
 * rendered in Blender) play the clip once. Skins that use the plain line
 * icons (Minimal Mono) draw each line on, like a pen. Every other skin just
 * shows its picture.
 *
 * [play] starts it; [onDone] is called when it finishes, so the caller can
 * remember it already played. When [play] is false the icon is just shown.
 */
@Composable
fun OpeningIcon(code: Int, isDay: Boolean, size: Dp, play: Boolean, onDone: () -> Unit) {
    val context = LocalContext.current
    // Android's "remove animations" setting turns this off too.
    val systemOff = remember {
        SystemSettings.Global.getFloat(context.contentResolver, SystemSettings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    }
    val run = play && !systemOff
    val skin = look.skin
    val clip = remember(skin.id, code, isDay) { clipFor(context, skin, code, isDay) }
    val (res, isArt) = remember(skin.id, code, isDay) { iconFor(context, skin, code, isDay) }
    var done by remember(play) { mutableStateOf(!run) }
    LaunchedEffect(play) { if (play && !run) onDone() }

    when {
        done -> WeatherIcon(code, isDay, size)
        clip != 0 -> ClipPlayer(clip, size) { done = true; onDone() }
        !isArt -> DrawOn(context, res, size) { done = true; onDone() }
        else -> {
            WeatherIcon(code, isDay, size)
            LaunchedEffect(Unit) { done = true; onDone() }
        }
    }
}

/** Plays an animated WebP once at [size], then calls [onEnd]. */
@Composable
private fun ClipPlayer(clip: Int, size: Dp, onEnd: () -> Unit) {
    val end by rememberUpdatedState(onEnd)
    AndroidView(
        modifier = Modifier.size(size),
        factory = { ctx ->
            ImageView(ctx).apply {
                scaleType = ImageView.ScaleType.FIT_CENTER
                val d = runCatching { ImageDecoder.decodeDrawable(ImageDecoder.createSource(ctx.resources, clip)) }.getOrNull()
                if (d is AnimatedImageDrawable) {
                    d.repeatCount = 0
                    d.registerAnimationCallback(object : Animatable2.AnimationCallback() {
                        override fun onAnimationEnd(drawable: Drawable?) = end()
                    })
                    setImageDrawable(d)
                    d.start()
                } else {
                    post { end() }
                }
            }
        },
    )
}

/**
 * Draws a line icon's strokes on one after another, like a pen tracing them,
 * in the skin's icon color, then calls [onEnd].
 */
@Composable
private fun DrawOn(context: Context, res: Int, size: Dp, onEnd: () -> Unit) {
    val end by rememberUpdatedState(onEnd)
    val icon = remember(res) { lineIcon(context, res) }
    if (icon == null) {
        WeatherIcon(0, true, size)
        LaunchedEffect(Unit) { end() }
        return
    }
    val t = remember { Animatable(0f) }
    LaunchedEffect(res) {
        t.animateTo(1f, tween(DRAW_MS, easing = LinearEasing))
        end()
    }
    val color = look.icon
    Canvas(Modifier.size(size)) {
        val k = this.size.minDimension / icon.viewport
        val total = icon.lengths.sum()
        var budget = t.value * total
        scale(k, k, pivot = androidx.compose.ui.geometry.Offset.Zero) {
            icon.paths.forEachIndexed { i, p ->
                val len = icon.lengths[i]
                if (budget <= 0f) return@forEachIndexed
                val part = Path()
                PathMeasure().apply { setPath(p, false) }.getSegment(0f, budget.coerceAtMost(len), part, true)
                drawPath(part, color, style = Stroke(icon.strokes[i], cap = StrokeCap.Round, join = StrokeJoin.Round))
                budget -= len
            }
        }
    }
}

private class LineIcon(val viewport: Float, val paths: List<Path>, val strokes: List<Float>, val lengths: List<Float>)

/** Reads a vector drawable's stroked paths so they can be drawn on bit by bit. */
private fun lineIcon(context: Context, res: Int): LineIcon? = runCatching {
    val xml = context.resources.getXml(res)
    val ns = "http://schemas.android.com/apk/res/android"
    var viewport = 24f
    val paths = mutableListOf<Path>()
    val strokes = mutableListOf<Float>()
    while (xml.next() != XmlPullParser.END_DOCUMENT) {
        if (xml.eventType != XmlPullParser.START_TAG) continue
        when (xml.name) {
            "vector" -> viewport = xml.getAttributeValue(ns, "viewportWidth")?.toFloatOrNull() ?: 24f
            "path" -> {
                val data = xml.getAttributeValue(ns, "pathData") ?: continue
                // Every subpath ("M...") is its own stroke, so each drop or
                // ray is drawn in turn.
                data.split(Regex("(?=[Mm])")).filter { it.isNotBlank() }.forEach { sub ->
                    paths += PathParser().parsePathString(sub).toPath()
                    strokes += xml.getAttributeValue(ns, "strokeWidth")?.toFloatOrNull() ?: 1.6f
                }
            }
        }
    }
    xml.close()
    val lengths = paths.map { p -> PathMeasure().apply { setPath(p, false) }.length }
    if (paths.isEmpty()) null else LineIcon(viewport, paths, strokes, lengths)
}.getOrNull()
