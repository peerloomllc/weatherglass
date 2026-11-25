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

    val kurosawa = Skin(
        id = "kurosawa", name = "Kurosawa",
        light = Palette(0xFF121212, 0xFF1E1C1A, 0x1FFFFFFF, 0xFFECE8E0, 0xFF8A8680, 0xFFC8102E, 0xFFECE8E0),
        font = Font.SERIF, corner = 0, upperLabels = true,
    )
    val anime = Skin(
        id = "anime", name = "Anime",
        light = Palette(0xFF5AB4F5, 0xFFBFE6FF, 0x59FFFFFF, 0xFF0F2C55, 0xFF2F5E94, 0xFFFF6B8B, 0xFF0F2C55),
        corner = 24,
    )
    val ukiyoe = Skin(
        id = "ukiyoe", name = "Ukiyo-e",
        light = Palette(0xFFF1E6CC, 0xFFE4D3AE, 0xFFF8F0DD, 0xFF1F2A44, 0xFF6B6A5E, 0xFFB5432F, 0xFF1F2A44),
        font = Font.SERIF, corner = 2,
    )
    val ink = Skin(
        id = "ink", name = "Ink wash",
        light = Palette(0xFFF5F1E8, 0xFFEAE4D6, 0xFFFBF8F2, 0xFF1A1A1A, 0xFF7A756C, 0xFFB22222, 0xFF1A1A1A),
        font = Font.SERIF, corner = 0,
    )

    val crt = Skin(
        id = "crt", name = "CRT Terminal",
        light = Palette(0xFF040A05, 0xFF07140A, 0xFF0B1F10, 0xFF33FF66, 0xFF1E9C45, 0xFFB3FFC6, 0xFF33FF66),
        font = Font.MONO, corner = 0, upperLabels = true,
    )
    val vapor = Skin(
        id = "vapor", name = "Vaporwave",
        light = Palette(0xFFFFB3DE, 0xFFA79BFF, 0x40FFFFFF, 0xFF2B1B4D, 0xFF5E4A8C, 0xFF007C8C, 0xFF2B1B4D),
        corner = 16, upperLabels = true,
    )
    val lcd = Skin(
        id = "lcd", name = "LCD watch",
        light = Palette(0xFFA3B18A, 0xFF8E9C76, 0x14000000, 0xFF1F2A1A, 0xFF4A5640, 0xFF1F2A1A, 0xFF1F2A1A),
        font = Font.MONO, corner = 4,
    )
    val teletext = Skin(
        id = "teletext", name = "Teletext",
        light = Palette(0xFF000000, 0xFF000000, 0xFF0000C8, 0xFFFFFFFF, 0xFF00FFFF, 0xFFFFFF00, 0xFFFFFFFF),
        font = Font.MONO, corner = 0, upperLabels = true,
    )

    val bauhaus = Skin(
        id = "bauhaus", name = "Bauhaus",
        light = Palette(0xFFF2EBDD, 0xFFE9DFCC, 0xFFFAF6EE, 0xFF111111, 0xFF5C5853, 0xFFD62828, 0xFF111111),
        corner = 0, upperLabels = true,
    )
    val deco = Skin(
        id = "deco", name = "Art Deco",
        light = Palette(0xFF101010, 0xFF1C1812, 0xFF1F1B14, 0xFFF3E5AB, 0xFFA8925A, 0xFFD4AF37, 0xFFD4AF37),
        font = Font.SERIF, corner = 0, upperLabels = true,
    )
    val riso = Skin(
        id = "riso", name = "Risograph",
        light = Palette(0xFFF6F1E7, 0xFFEFE8DA, 0xFFFBF8F1, 0xFF1A2B6B, 0xFF5A6A9A, 0xFFE0218A, 0xFF0078BF),
        corner = 6, upperLabels = true,
    )
    val blueprint = Skin(
        id = "blueprint", name = "Blueprint",
        light = Palette(0xFF0D5596, 0xFF0A4275, 0x1FFFFFFF, 0xFFFFFFFF, 0xFFA9C6E8, 0xFFFFD54F, 0xFFFFFFFF),
        font = Font.MONO, corner = 0, upperLabels = true,
    )

    val watercolor = Skin(
        id = "watercolor", name = "Watercolor",
        light = Palette(0xFFFBF8F2, 0xFFF1ECE2, 0xFFFFFFFF, 0xFF2E3A4F, 0xFF7A8597, 0xFF3C7FC1, 0xFF2E3A4F),
        font = Font.SERIF, corner = 14,
    )
    val clay = Skin(
        id = "clay", name = "Claymation",
        light = Palette(0xFFEDE8DE, 0xFFE0D9CC, 0xFFF7F3EC, 0xFF3B3530, 0xFF85796D, 0xFFF28C28, 0xFF3B3530),
        corner = 28,
    )
    val felt = Skin(
        id = "felt", name = "Felt",
        light = Palette(0xFF2F5D62, 0xFF264C50, 0x26FFFFFF, 0xFFF4EFE6, 0xFFB8CBC6, 0xFFE8A33D, 0xFFF4EFE6),
        corner = 18,
    )
    val chalk = Skin(
        id = "chalk", name = "Chalkboard",
        light = Palette(0xFF2E4A3A, 0xFF27402F, 0x1FFFFFFF, 0xFFF4F4EC, 0xFFB5C4B8, 0xFFF7E37A, 0xFFF4F4EC),
        corner = 4,
    )

    val barometer = Skin(
        id = "barometer", name = "Ship's barometer",
        light = Palette(0xFF13233A, 0xFF0E1A2B, 0xFF1A2E4A, 0xFFEFE6D2, 0xFF9FA8B5, 0xFFC9A15B, 0xFFC9A15B),
        font = Font.SERIF, corner = 10,
    )
    val journal = Skin(
        id = "journal", name = "Field journal",
        light = Palette(0xFFF3EAD7, 0xFFEADFC6, 0xFFF8F1E2, 0xFF4A3526, 0xFF8A7560, 0xFF8C5A2B, 0xFF4A3526),
        font = Font.SERIF, corner = 2,
    )
    val noir = Skin(
        id = "noir", name = "Noir",
        light = Palette(0xFF0B0B0B, 0xFF1C1C1C, 0x1AFFFFFF, 0xFFF0F0F0, 0xFF8C8C8C, 0xFFFFFFFF, 0xFFF0F0F0),
        font = Font.SERIF, corner = 0, upperLabels = true,
    )
    val lofi = Skin(
        id = "lofi", name = "Lo-fi",
        light = Palette(0xFF2B2440, 0xFF4A3B5C, 0x26FFFFFF, 0xFFF4E9E1, 0xFFB9A8C4, 0xFFFFB27A, 0xFFF4E9E1),
        corner = 20,
    )
    val terrarium = Skin(
        id = "terrarium", name = "Terrarium",
        light = Palette(0xFFE7EFE4, 0xFFD5E3D0, 0xFFF4F8F2, 0xFF24402F, 0xFF6A8573, 0xFF3F7D4E, 0xFF24402F),
        corner = 22,
    )

    val rpg = Skin(
        id = "rpg", name = "16-bit RPG",
        light = Palette(0xFF1B2A6B, 0xFF0E1640, 0xFF2A3D8F, 0xFFFFFFFF, 0xFFB8C4F0, 0xFFFFD34D, 0xFFFFFFFF),
        font = Font.MONO, corner = 6,
    )
    val dice = Skin(
        id = "dice", name = "Tabletop dice",
        light = Palette(0xFFEFE3C6, 0xFFE3D2AC, 0xFFF6EDD8, 0xFF3B2A1A, 0xFF7D6A52, 0xFFB23A48, 0xFF3B2A1A),
        font = Font.SERIF, corner = 8,
    )
    val iso = Skin(
        id = "iso", name = "Isometric town",
        light = Palette(0xFFDDEBF5, 0xFFF1F5EC, 0xB3FFFFFF, 0xFF22313F, 0xFF62727F, 0xFF4E9A45, 0xFF22313F),
        corner = 16,
    )
    val gauge = Skin(
        id = "gauge", name = "Round gauge",
        light = Palette(0xFF20242B, 0xFF15181D, 0xFF2A2F38, 0xFFF2EEE6, 0xFF9AA3AE, 0xFFE8B04A, 0xFFF2EEE6),
        corner = 12,
    )

    val all = listOf(
        mono, paper, pixel, retro, kurosawa, anime, ukiyoe, ink, crt, vapor, lcd, teletext,
        bauhaus, deco, riso, blueprint, watercolor, clay, felt, chalk,
        barometer, journal, noir, lofi, terrarium, rpg, dice, iso, gauge,
    )
    /** The skin picker's groups, in order. Every skin is in exactly one. */
    val groups = listOf(
        "Simple" to listOf(mono),
        "Retro and games" to listOf(pixel, rpg, retro, crt, vapor, lcd, teletext, dice),
        "Art and print" to listOf(kurosawa, noir, anime, ukiyoe, ink, bauhaus, deco, riso, blueprint),
        "Hand-made" to listOf(paper, watercolor, clay, felt, chalk, journal),
        "Places and objects" to listOf(barometer, gauge, terrarium, iso, lofi),
    )

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
/** Icons smaller than this use a skin's "_mini" pictures when it has them. */
const val MINI_BELOW_DP = 40

/**
 * The picture for a weather code in a skin, and whether it is the skin's own
 * art (true) or a built-in line icon to tint (false). Skins that draw the
 * weather inside something (a jar, a die, a dial) also ship a "_mini" set
 * with just the weather, used when [small] is true so it stays readable.
 */
fun iconFor(context: Context, skin: Skin, code: Int, isDay: Boolean, small: Boolean = false): Pair<Int, Boolean> {
    val name = "skin_${skin.id}_${artKey(conditionFor(code))}_${if (isDay) "day" else "night"}"
    val res = context.resources
    val art = (if (small) res.getIdentifier(name + "_mini", "drawable", context.packageName) else 0)
        .takeIf { it != 0 } ?: res.getIdentifier(name, "drawable", context.packageName)
    return if (art != 0) art to true else builtinIcon(code, isDay) to false
}
