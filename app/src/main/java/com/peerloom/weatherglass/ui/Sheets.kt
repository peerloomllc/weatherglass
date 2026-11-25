package com.peerloom.weatherglass.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.peerloom.weatherglass.R
import com.peerloom.weatherglass.data.Place
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.data.TempUnit
import com.peerloom.weatherglass.data.WindUnit
import com.peerloom.weatherglass.skin.Skins

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Sheet(onDismiss: () -> Unit, content: @Composable () -> Unit) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = look.bgTop,
        contentColor = look.text,
        shape = RoundedCornerShape(topStart = look.skin.corner.coerceAtLeast(8).dp, topEnd = look.skin.corner.coerceAtLeast(8).dp),
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp).navigationBarsPadding().padding(bottom = 16.dp)) { content() }
    }
}

@Composable
fun PlacesSheet(
    state: UiState,
    onDismiss: () -> Unit,
    onSelect: (Int) -> Unit,
    onRemove: (Int) -> Unit,
    onAdd: (Place) -> Unit,
    onUseLocation: () -> Unit,
    onSearch: (String) -> Unit,
) = Sheet(onDismiss) {
    var query by remember { mutableStateOf("") }
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        T(look.label("Places"), 20.sp, weight = FontWeight.Medium)
        state.places.forEachIndexed { i, p ->
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp)))
                    .background(if (i == state.selected) look.card else Color.Transparent)
                    .clickable { onSelect(i) }.padding(start = 14.dp, top = 4.dp, bottom = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (p.isCurrent) {
                    Image(painterResource(R.drawable.ic_location), null, Modifier.size(18.dp), colorFilter = ColorFilter.tint(look.text))
                    Spacer(Modifier.width(8.dp))
                }
                Column(Modifier.weight(1f).padding(vertical = 8.dp)) {
                    T(p.name, 17.sp)
                    if (p.region.isNotEmpty()) T(p.region, 13.sp, look.subtle)
                }
                SmallIcon(R.drawable.ic_close, "Remove ${p.name}") { onRemove(i) }
            }
        }
        if (state.places.none { it.isCurrent }) {
            Button(look.label("Use my location"), onClick = onUseLocation)
        }
        Spacer(Modifier.height(4.dp))
        BasicTextField(
            value = query,
            onValueChange = { query = it; onSearch(it) },
            singleLine = true,
            textStyle = TextStyle(color = look.text, fontSize = 17.sp, fontFamily = look.font),
            cursorBrush = SolidColor(look.accent),
            decorationBox = { inner ->
                Box(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp))).background(look.card).padding(16.dp),
                ) {
                    if (query.isEmpty()) T("Search for a city", 17.sp, look.subtle)
                    inner()
                }
            },
        )
        if (state.searching) T("Searching...", 14.sp, look.subtle)
        if (!state.searching && query.trim().length >= 2 && state.searchResults.isEmpty()) T("No places found", 14.sp, look.subtle)
        state.searchResults.forEach { p ->
            Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable { onAdd(p) }.padding(horizontal = 14.dp, vertical = 10.dp)) {
                T(p.name, 17.sp)
                if (p.region.isNotEmpty()) T(p.region, 13.sp, look.subtle)
            }
        }
    }
}

@Composable
fun SettingsSheet(settings: Settings, onDismiss: () -> Unit, onChange: (Settings) -> Unit) = Sheet(onDismiss) {
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        T(look.label("Settings"), 20.sp, weight = FontWeight.Medium)
        T(look.label("Skin"), 13.sp, look.subtle)
        val dark = isSystemInDarkTheme()
        Skins.all.chunked(2).forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                row.forEach { skin ->
                    val p = skin.palette(dark)
                    val picked = skin.id == settings.skin
                    CompositionLocalProvider(LocalLook provides Look(skin, p)) {
                        Column(
                            Modifier.weight(1f).clip(RoundedCornerShape(16.dp))
                                .background(Color(p.bgTop))
                                .border(if (picked) 3.dp else 1.dp, if (picked) Color(p.accent) else Color(p.subtle).copy(alpha = 0.4f), RoundedCornerShape(16.dp))
                                .clickable { onChange(settings.copy(skin = skin.id)) }.padding(14.dp),
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                WeatherIcon(2, true, 32.dp)
                                Spacer(Modifier.width(8.dp))
                                T("72°", 24.sp, weight = FontWeight.Light)
                            }
                            Spacer(Modifier.height(6.dp))
                            T(look.label(skin.name), 14.sp, weight = FontWeight.Medium, maxLines = 1)
                        }
                    }
                }
            }
        }
        T(look.label("Temperature"), 13.sp, look.subtle)
        Choice(listOf("°F" to TempUnit.F, "°C" to TempUnit.C), settings.tempUnit) { onChange(settings.copy(tempUnit = it)) }
        T(look.label("Wind"), 13.sp, look.subtle)
        Choice(WindUnit.entries.map { it.label to it }, settings.windUnit) { onChange(settings.copy(windUnit = it)) }
        T(look.label("Clock"), 13.sp, look.subtle)
        Choice(listOf("12 hour" to false, "24 hour" to true), settings.use24h) { onChange(settings.copy(use24h = it)) }
        T(look.label("Severe weather alerts (US)"), 13.sp, look.subtle)
        Choice(listOf("On" to true, "Off" to false), settings.alerts) { onChange(settings.copy(alerts = it)) }
        T("Weather data by Open-Meteo.com (CC BY 4.0). Alerts from the US National Weather Service. Your location is only sent to them to get your forecast.", 12.sp, look.subtle)
    }
}

@Composable
private fun <V> Choice(options: List<Pair<String, V>>, value: V, onPick: (V) -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(14.dp))).background(look.card).padding(4.dp),
    ) {
        options.forEach { (label, v) ->
            val on = v == value
            Box(
                Modifier.weight(1f).clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(10.dp)))
                    .background(if (on) look.accent else Color.Transparent).clickable { onPick(v) }.padding(vertical = 10.dp),
                contentAlignment = Alignment.Center,
            ) { T(label, 15.sp, if (on) look.bgTop else look.text, if (on) FontWeight.Medium else FontWeight.Normal) }
        }
    }
}
