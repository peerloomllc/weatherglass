package com.peerloom.weatherglass.ui

import com.peerloom.weatherglass.skin.Skin
import com.peerloom.weatherglass.data.AlertKind
import com.peerloom.weatherglass.skin.Palette
import androidx.compose.ui.draw.rotate
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.foundation.layout.RowScope
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.AnimatedVisibility
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
internal fun Sheet(onDismiss: () -> Unit, content: @Composable () -> Unit) {
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
        if (state.searching) T("Searching…", 14.sp, look.subtle)
        if (!state.searching && query.trim().length >= 2 && state.searchResults.isEmpty()) T("No matching places", 14.sp, look.subtle)
        state.searchResults.forEach { p ->
            Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable { onAdd(p) }.padding(horizontal = 14.dp, vertical = 10.dp)) {
                T(p.name, 17.sp)
                if (p.region.isNotEmpty()) T(p.region, 13.sp, look.subtle)
            }
        }
    }
}

@Composable
fun SettingsSheet(settings: Settings, onDismiss: () -> Unit, onChange: (Settings) -> Unit, onAbout: () -> Unit) = Sheet(onDismiss) {
    val current = Skins.byId(settings.skin)
    // One section open at a time, like the skin groups and the About page.
    var openSection by rememberSaveable { mutableStateOf<String?>(null) }
    fun toggle(id: String) { openSection = if (openSection == id) null else id }
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        T(look.label("Settings"), 20.sp, weight = FontWeight.Medium)

        Section("Skin", current.name, openSection == "skin", { toggle("skin") }) {
            // One group open at a time; the current skin's group starts open.
            var openGroup by rememberSaveable { mutableStateOf(Skins.groups.firstOrNull { current in it.second }?.first) }
            Skins.groups.forEach { (name, skins) ->
                SkinGroup(name, skins, settings, onChange, open = openGroup == name) {
                    openGroup = if (openGroup == name) null else name
                }
            }
            RequestSkinCard()
        }

        Section("Opening animation", if (settings.animate) "On" else "Off", openSection == "motion", { toggle("motion") }) {
            Choice(listOf("On" to true, "Off" to false), settings.animate) { onChange(settings.copy(animate = it)) }
            T("Plays once when the app opens, in the skin's own style. Stays off if animations are turned off in Android's settings.", 12.sp, look.subtle)
        }

        val units = listOf(
            if (settings.tempUnit == TempUnit.F) "°F" else "°C",
            settings.windUnit.label,
            if (settings.use24h) "24 hour" else "12 hour",
        ).joinToString("  ·  ")
        Section("Units", units, openSection == "units", { toggle("units") }) {
            T(look.label("Temperature"), 13.sp, look.subtle)
            Choice(listOf("°F" to TempUnit.F, "°C" to TempUnit.C), settings.tempUnit) { onChange(settings.copy(tempUnit = it)) }
            T(look.label("Wind"), 13.sp, look.subtle)
            Choice(WindUnit.entries.map { it.label to it }, settings.windUnit) { onChange(settings.copy(windUnit = it)) }
            T(look.label("Clock"), 13.sp, look.subtle)
            Choice(listOf("12 hour" to false, "24 hour" to true), settings.use24h) { onChange(settings.copy(use24h = it)) }
        }

        val on = listOfNotNull(
            "Severe weather".takeIf { settings.alerts },
            "Freeze tonight".takeIf { settings.freezeAlert },
            "Rain soon".takeIf { settings.rainSoonAlert },
        )
        Section("Alerts", on.joinToString("  ·  ").ifEmpty { "Off" }, openSection == "alerts", { toggle("alerts") }) {
            T(look.label("Severe weather (US)"), 13.sp, look.subtle)
            Choice(listOf("On" to true, "Off" to false), settings.alerts) { onChange(settings.copy(alerts = it)) }
            T("Official warnings from the US National Weather Service, at the top of the screen and as a notification.", 12.sp, look.subtle)
            if (settings.alerts) {
                T("Notify me about", 12.sp, look.subtle)
                AlertKind.entries.forEach { k ->
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        T(k.label, 14.sp, modifier = Modifier.weight(1f))
                        Box(Modifier.width(150.dp)) {
                            Choice(listOf("On" to true, "Off" to false), k !in settings.mutedKinds) { on ->
                                onChange(settings.copy(mutedKinds = if (on) settings.mutedKinds - k else settings.mutedKinds + k))
                            }
                        }
                    }
                }
                T("Groups switched off still show at the top of the screen, without a notification.", 12.sp, look.subtle)
            }

            Spacer(Modifier.height(4.dp))
            T(look.label("Freeze tonight"), 13.sp, look.subtle)
            Choice(listOf("On" to true, "Off" to false), settings.freezeAlert) { onChange(settings.copy(freezeAlert = it)) }
            if (settings.freezeAlert) {
                val f = settings.tempUnit == TempUnit.F
                T("Alert when the low reaches", 12.sp, look.subtle)
                Choice(
                    listOf((if (f) "32°F" else "0°C") to 0.0, (if (f) "36°F (frost)" else "2°C (frost)") to 2.0),
                    settings.freezeAtC,
                ) { onChange(settings.copy(freezeAtC = it)) }
            }
            T("One note in the evening when tonight's low will reach this.", 12.sp, look.subtle)

            Spacer(Modifier.height(4.dp))
            T(look.label("Rain starting soon"), 13.sp, look.subtle)
            Choice(listOf("On" to true, "Off" to false), settings.rainSoonAlert) { onChange(settings.copy(rainSoonAlert = it)) }
            T("A note up to an hour before rain or snow starts. Quiet from 10 pm to 7 am. Checks every 15 minutes while on, which uses a little more battery.", 12.sp, look.subtle)
        }

        Row(
            Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp))).background(look.card)
                .clickable(onClick = onAbout).padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            T(look.label("About Weatherglass"), 15.sp, weight = FontWeight.Medium, modifier = Modifier.weight(1f))
            T("›", 22.sp, look.subtle)
        }

        Spacer(Modifier.height(4.dp))
        T("Weather data by Open-Meteo.com (CC BY 4.0). Alerts from the US National Weather Service.", 12.sp, look.subtle)
    }
}

/** A settings section: a header showing its current value, which opens to show its controls. */
@Composable
private fun Section(title: String, summary: String, open: Boolean, onToggle: () -> Unit, content: @Composable () -> Unit) {
    Column(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(look.skin.corner.dp.coerceAtMost(16.dp))).background(look.card),
    ) {
        Row(
            Modifier.fillMaxWidth().clickable(onClick = onToggle).padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                T(look.label(title), 15.sp, weight = FontWeight.Medium)
                if (!open) T(summary, 13.sp, look.subtle, maxLines = 1)
            }
            Chevron(open)
        }
        AnimatedVisibility(open) {
            Column(Modifier.padding(start = 16.dp, end = 16.dp, bottom = 16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                content()
            }
        }
    }
}

@Composable
private fun Chevron(open: Boolean) {
    val turn by animateFloatAsState(if (open) 90f else 0f, label = "chevron")
    T("›", 22.sp, look.subtle, modifier = Modifier.rotate(turn))
}

/** One group of skins in the picker, opened or closed by its header (the picker keeps one open at a time). */
@Composable
private fun SkinGroup(name: String, skins: List<Skin>, settings: Settings, onChange: (Settings) -> Unit, open: Boolean, onToggle: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp)).clickable(onClick = onToggle).padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        T(look.label(name), 13.sp, look.subtle, modifier = Modifier.weight(1f))
        T("${skins.size}", 13.sp, look.subtle)
        Spacer(Modifier.width(8.dp))
        Chevron(open)
    }
    AnimatedVisibility(open) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            val dark = isSystemInDarkTheme()
            skins.chunked(2).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    row.forEach { skin -> SkinCard(skin, skin.palette(dark), skin.id == settings.skin) { onChange(settings.copy(skin = skin.id)) } }
                    if (row.size == 1) Spacer(Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun RowScope.SkinCard(skin: Skin, p: Palette, picked: Boolean, onPick: () -> Unit) {
    CompositionLocalProvider(LocalLook provides Look(skin, p)) {
        Column(
            Modifier.weight(1f).clip(RoundedCornerShape(16.dp))
                .background(Color(p.bgTop))
                .border(if (picked) 3.dp else 1.dp, if (picked) Color(p.accent) else Color(p.subtle).copy(alpha = 0.4f), RoundedCornerShape(16.dp))
                .clickable(onClick = onPick).padding(14.dp),
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

/** "Request a skin": opens an email to PeerLoom with a short template. No server. */
@Composable
private fun RequestSkinCard() {
    val context = androidx.compose.ui.platform.LocalContext.current
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
            .border(1.dp, look.subtle.copy(alpha = 0.5f), RoundedCornerShape(16.dp))
            .clickable { requestSkin(context) }.padding(14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            T(look.label("Request a skin"), 14.sp, weight = FontWeight.Medium)
            T("Have an idea for a look? Tell us and we may make it.", 12.sp, look.subtle)
        }
        T("›", 22.sp, look.subtle)
    }
}

private fun requestSkin(context: android.content.Context) {
    val subject = "[Weatherglass] Skin request"
    val body = """Skin name:

Look or theme (what should it feel like?):

Colours:

Link to a reference picture (optional):

Anything else:
"""
    val uri = android.net.Uri.parse(
        "mailto:peerloomllc@proton.me?subject=" + android.net.Uri.encode(subject) + "&body=" + android.net.Uri.encode(body),
    )
    val send = android.content.Intent(android.content.Intent.ACTION_SENDTO, uri)
        .putExtra(android.content.Intent.EXTRA_SUBJECT, subject)
        .putExtra(android.content.Intent.EXTRA_TEXT, body)
        .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
    runCatching { context.startActivity(send) }.onFailure {
        android.widget.Toast.makeText(context, "No email app found. Write to peerloomllc@proton.me", android.widget.Toast.LENGTH_LONG).show()
    }
}
