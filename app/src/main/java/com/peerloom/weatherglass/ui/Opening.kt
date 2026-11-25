package com.peerloom.weatherglass.ui

import com.peerloom.weatherglass.skin.clipFor
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.getValue
import androidx.compose.ui.viewinterop.AndroidView
import android.widget.ImageView
import android.graphics.drawable.Drawable
import android.graphics.drawable.Animatable2
import android.graphics.drawable.AnimatedImageDrawable
import android.graphics.ImageDecoder
import android.provider.Settings as SystemSettings
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import com.peerloom.weatherglass.data.Condition
import com.peerloom.weatherglass.data.conditionFor
import kotlin.math.PI
import kotlin.math.sin

/** How long the opening animation runs, in milliseconds. */
const val OPENING_MS = 1500

/**
 * The big weather icon, animated once when the app opens. Skins with
 * opening clips (res/raw/clip_<skin>_<weather>_<day|night>.webp, rendered
 * in Blender) play the clip once. Every other skin gets motion in code: it rises and
 * fades in, the sun turns into place, clouds and fog drift in, rain and
 * snow fall in the skin's icon color, and thunder flickers. Works the same
 * for every skin because it moves the skin's own picture.
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
    val useClip = run && clip != 0
    var clipDone by remember(play) { mutableStateOf(false) }
    if (useClip && !clipDone) {
        ClipPlayer(clip, size) {
            clipDone = true
            onDone()
        }
        return
    }
    val t = remember { Animatable(if (run && !useClip) 0f else 1f) }
    LaunchedEffect(run) {
        if (run && !useClip) {
            t.snapTo(0f)
            t.animateTo(1f, tween(OPENING_MS, easing = LinearEasing))
        } else {
            t.snapTo(1f)
        }
        if (play && !useClip) onDone()
    }

    val v = t.value
    val cond = conditionFor(code)
    // Entrance over the first 40%: rise, grow and fade in.
    val e = FastOutSlowInEasing.transform((v / 0.4f).coerceIn(0f, 1f))
    val px = with(LocalDensity.current) { size.toPx() }
    val drifts = cond == Condition.PARTLY_CLOUDY || cond == Condition.CLOUDY || cond == Condition.FOG
    val turns = cond == Condition.CLEAR && isDay
    // Thunder: two quick flickers part way through.
    val flicker = if (cond == Condition.THUNDER && (v in 0.5f..0.56f || v in 0.63f..0.67f)) 0.45f else 1f
    val tint = look.icon

    Box(Modifier.size(size)) {
        Box(
            Modifier.graphicsLayer {
                alpha = e * flicker
                val sc = 0.82f + 0.18f * e
                scaleX = sc
                scaleY = sc
                translationY = (1 - e) * px * 0.12f
                translationX = if (drifts) (1 - e) * -px * (if (cond == Condition.FOG) 0.25f else 0.15f) else 0f
                rotationZ = if (turns) (1 - e) * -40f else 0f
            },
        ) { WeatherIcon(code, isDay, size) }

        val falling = when (cond) {
            Condition.RAIN, Condition.DRIZZLE, Condition.SLEET, Condition.SNOW, Condition.THUNDER -> true
            else -> false
        }
        if (falling && v < 1f) {
            Canvas(Modifier.size(size)) {
                val w = this.size.width
                val h = this.size.height
                val count = if (cond == Condition.DRIZZLE) 8 else 14
                for (i in 0 until count) {
                    val x = w * (0.15f + 0.7f * ((i * 0.618f) % 1f))
                    val delay = (i % 7) / 7f * 0.45f
                    val p = ((v - 0.25f - delay) / 0.4f).coerceIn(0f, 1f)
                    if (p <= 0f || p >= 1f) continue
                    val y = h * (0.5f + 0.55f * p)
                    val a = (sin(PI * p).toFloat() * 0.85f)
                    val snowy = cond == Condition.SNOW || (cond == Condition.SLEET && i % 2 == 0)
                    if (snowy) {
                        val wobble = sin((p * 6f + i).toDouble()).toFloat() * w * 0.02f
                        drawCircle(tint.copy(alpha = a), radius = w * 0.018f, center = Offset(x + wobble, y))
                    } else {
                        val len = h * (if (cond == Condition.DRIZZLE) 0.035f else 0.07f)
                        drawLine(
                            tint.copy(alpha = a), Offset(x + len * 0.25f, y - len), Offset(x, y),
                            strokeWidth = w * 0.014f, cap = StrokeCap.Round,
                        )
                    }
                }
            }
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
