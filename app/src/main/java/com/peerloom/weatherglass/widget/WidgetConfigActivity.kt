package com.peerloom.weatherglass.widget

import android.appwidget.AppWidgetManager
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.appwidget.GlanceAppWidgetManager
import androidx.glance.appwidget.state.getAppWidgetState
import androidx.glance.appwidget.state.updateAppWidgetState
import androidx.glance.state.PreferencesGlanceStateDefinition
import androidx.datastore.preferences.core.Preferences
import androidx.lifecycle.lifecycleScope
import com.peerloom.weatherglass.data.Prefs
import com.peerloom.weatherglass.skin.Skins
import com.peerloom.weatherglass.ui.Button
import com.peerloom.weatherglass.ui.LocalLook
import com.peerloom.weatherglass.ui.Look
import com.peerloom.weatherglass.ui.T
import com.peerloom.weatherglass.ui.look
import kotlinx.coroutines.launch

// Opens when a Weatherglass widget is added, and again from the home
// screen's widget settings. Picks which parts the widget shows.
class WidgetConfigActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val appWidgetId = intent?.extras?.getInt(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
            ?: AppWidgetManager.INVALID_APPWIDGET_ID
        // Backing out without saving cancels adding the widget.
        setResult(RESULT_CANCELED, Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId))
        val info = AppWidgetManager.getInstance(this).getAppWidgetInfo(appWidgetId)
        val widget = Widgets.byReceiver(info?.provider?.className)
        if (appWidgetId == AppWidgetManager.INVALID_APPWIDGET_ID || widget == null) { finish(); return }
        val glanceId = GlanceAppWidgetManager(this).getGlanceIdBy(appWidgetId)
        enableEdgeToEdge()

        lifecycleScope.launch {
            val state = getAppWidgetState<Preferences>(this@WidgetConfigActivity, PreferencesGlanceStateDefinition, glanceId)
            val initial = widget.parts(state)
            setContent {
                val skin = Skins.byId(Prefs(this@WidgetConfigActivity).settings.skin)
                val lk = Look(skin, skin.palette(isSystemInDarkTheme()))
                var picked by remember { mutableStateOf(initial) }
                CompositionLocalProvider(LocalLook provides lk) {
                    Column(
                        Modifier.fillMaxSize().background(lk.bgTop).statusBarsPadding().navigationBarsPadding()
                            .padding(20.dp).verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        T(lk.label("Widget"), 24.sp, weight = FontWeight.Medium)
                        T("Choose what this widget shows. Parts that don't fit its size are left out.", 15.sp, look.subtle)
                        Spacer(Modifier.height(6.dp))
                        Part.entries.forEach { part ->
                            val on = part in picked
                            Row(
                                Modifier.fillMaxWidth().clip(RoundedCornerShape(skin.corner.coerceAtMost(16).dp)).background(lk.card)
                                    .clickable { picked = if (on) picked - part else picked + part }.padding(16.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                T(part.label, 17.sp, modifier = Modifier.weight(1f))
                                Box(
                                    Modifier.size(24.dp).clip(RoundedCornerShape(if (skin.corner == 0) 0.dp else 6.dp))
                                        .background(if (on) lk.accent else Color.Transparent)
                                        .then(if (on) Modifier else Modifier.background(lk.subtle.copy(alpha = 0.3f))),
                                    contentAlignment = Alignment.Center,
                                ) { if (on) T("✓", 16.sp, lk.bgTop, FontWeight.Bold) }
                            }
                        }
                        Spacer(Modifier.height(10.dp))
                        Button(lk.label("Done"), primary = true) {
                            lifecycleScope.launch {
                                updateAppWidgetState(this@WidgetConfigActivity, glanceId) { prefs ->
                                    Part.entries.forEach { prefs[partKey(it)] = it in picked }
                                }
                                Widgets.bump(this@WidgetConfigActivity, widget, glanceId)
                                setResult(RESULT_OK, Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId))
                                finish()
                            }
                        }
                    }
                }
            }
        }
    }
}
