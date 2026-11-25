package com.peerloom.weatherglass.skin

import android.annotation.SuppressLint
import android.content.Context
import com.peerloom.weatherglass.R
import com.peerloom.weatherglass.data.Condition
import com.peerloom.weatherglass.data.conditionFor

// A skin is the colors, type and pictures shared by the app screen and the
// widgets, so one switch changes both.
//
// Pictures: a skin's own art goes in res/drawable as
// skin_<id>_<weather>_<day|night> (for example skin_paper_rain_day.png),
// rendered ahead of time in Blender. Any picture a skin does not have yet
// falls back to the built-in line icon, drawn in the skin's icon color.

enum class Font { SANS, SERIF, MONO }

data class Palette(
    val bgTop: Long,
    val bgBottom: Long,
    val card: Long,
    val text: Long,
    val subtle: Long,
    val accent: Long,
    val icon: Long,
)

data class Skin(
    val id: String,
    val name: String,
    val light: Palette,
    val dark: Palette = light,
    val font: Font = Font.SANS,
    val corner: Int = 20, // dp
    val upperLabels: Boolean = false,
    val followsSystem: Boolean = false,
) {
    fun palette(systemDark: Boolean) = if (followsSystem && systemDark) dark else light
}

object Skins {
    val mono = Skin(
        id = "mono", name = "Minimal Mono",
        light = Palette(0xFFFFFFFF, 0xFFFFFFFF, 0xFFF2F2F2, 0xFF111111, 0xFF6B6B6B, 0xFF111111, 0xFF111111),
        dark = Palette(0xFF000000, 0xFF000000, 0xFF161616, 0xFFF5F5F5, 0xFF9A9A9A, 0xFFF5F5F5, 0xFFF5F5F5),
        followsSystem = true,
    )
    val paper = Skin(
        id = "paper", name = "Paper cut",
        light = Palette(0xFFF4ECDD, 0xFFE8DBC3, 0xFFFBF6EC, 0xFF3F3123, 0xFF8A765F, 0xFFC4623A, 0xFF5E4A34),
        font = Font.SERIF, corner = 6,
    )
    val pixel = Skin(
        id = "pixel", name = "8-bit",
        light = Palette(0xFF1C1F4A, 0xFF2B1F55, 0xFF2E3370, 0xFFF4F4F4, 0xFFA3A8D9, 0xFFFFCC33, 0xFFFFCC33),
        font = Font.MONO, corner = 0, upperLabels = true,
    )
    val retro = Skin(
        id = "retro", name = "Retro-future",
        light = Palette(0xFF1A0B2E, 0xFF3B0F4F, 0x33FFFFFF, 0xFFF9EAFF, 0xFFC7A6D9, 0xFFFF5FA2, 0xFF2DE2E6),
        corner = 28, upperLabels = true,
    )

    val all = listOf(mono, paper, pixel, retro)
    fun byId(id: String?) = all.firstOrNull { it.id == id } ?: mono
}

private fun artKey(c: Condition) = when (c) {
    Condition.CLEAR -> "clear"
    Condition.PARTLY_CLOUDY -> "partly"
    Condition.CLOUDY -> "cloudy"
    Condition.FOG -> "fog"
    Condition.DRIZZLE -> "drizzle"
    Condition.RAIN -> "rain"
    Condition.SLEET -> "sleet"
    Condition.SNOW -> "snow"
    Condition.THUNDER -> "thunder"
}

fun builtinIcon(code: Int, isDay: Boolean): Int = when (conditionFor(code)) {
    Condition.CLEAR -> if (isDay) R.drawable.wx_clear else R.drawable.wx_clear_night
    Condition.PARTLY_CLOUDY -> if (isDay) R.drawable.wx_partly else R.drawable.wx_partly_night
    Condition.CLOUDY -> R.drawable.wx_cloudy
    Condition.FOG -> R.drawable.wx_fog
    Condition.DRIZZLE -> R.drawable.wx_drizzle
    Condition.RAIN -> R.drawable.wx_rain
    Condition.SLEET -> R.drawable.wx_sleet
    Condition.SNOW -> R.drawable.wx_snow
    Condition.THUNDER -> R.drawable.wx_thunder
}

// Returns the drawable and whether it is skin art (shown as is) or the
// built-in line icon (tinted with the skin's icon color).
@SuppressLint("DiscouragedApi")
fun iconFor(context: Context, skin: Skin, code: Int, isDay: Boolean): Pair<Int, Boolean> {
    val name = "skin_${skin.id}_${artKey(conditionFor(code))}_${if (isDay) "day" else "night"}"
    val art = context.resources.getIdentifier(name, "drawable", context.packageName)
    return if (art != 0) art to true else builtinIcon(code, isDay) to false
}
