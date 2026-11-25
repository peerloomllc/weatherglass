package com.peerloom.weatherglass.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import com.peerloom.weatherglass.skin.Font
import com.peerloom.weatherglass.skin.Palette
import com.peerloom.weatherglass.skin.Skin

data class Look(val skin: Skin, val p: Palette) {
    val bgTop get() = Color(p.bgTop)
    val bgBottom get() = Color(p.bgBottom)
    val card get() = Color(p.card)
    val text get() = Color(p.text)
    val subtle get() = Color(p.subtle)
    val accent get() = Color(p.accent)
    val icon get() = Color(p.icon)
    val font get() = when (skin.font) {
        Font.SANS -> FontFamily.SansSerif
        Font.SERIF -> FontFamily.Serif
        Font.MONO -> FontFamily.Monospace
    }
    fun label(s: String) = if (skin.upperLabels) s.uppercase() else s
}

val LocalLook = staticCompositionLocalOf<Look> { error("no look") }

val look: Look @Composable get() = LocalLook.current
