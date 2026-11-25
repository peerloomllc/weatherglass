package com.peerloom.weatherglass.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.graphics.toArgb
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.peerloom.weatherglass.skin.Skins
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private val vm: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Refresh whenever the app comes to the front. The view model skips
        // the network if the forecast is under 10 minutes old.
        lifecycleScope.launch { repeatOnLifecycle(Lifecycle.State.STARTED) { vm.refresh() } }
        setContent {
            val state by vm.state.collectAsStateWithLifecycle()
            val skin = Skins.byId(state.settings.skin)
            val lk = Look(skin, skin.palette(isSystemInDarkTheme()))
            val darkBg = Color(lk.p.bgTop).luminance() < 0.5f
            LaunchedEffect(darkBg) {
                val bar = if (darkBg) SystemBarStyle.dark(Color.Transparent.toArgb())
                else SystemBarStyle.light(Color.Transparent.toArgb(), Color.Transparent.toArgb())
                enableEdgeToEdge(bar, bar)
            }
            val askLocation = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
                if (ok) vm.addCurrentLocation()
            }
            val askNotify = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
            // Alerts are on by default, so ask for notifications once, right
            // after the first place is added. Never again after that.
            val hasPlace = state.places.isNotEmpty()
            LaunchedEffect(hasPlace) {
                val prefs = getSharedPreferences("weatherglass", MODE_PRIVATE)
                if (hasPlace && state.settings.alerts && !prefs.getBoolean("askedNotify", false) &&
                    checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                ) {
                    prefs.edit().putBoolean("askedNotify", true).apply()
                    askNotify.launch(Manifest.permission.POST_NOTIFICATIONS)
                }
            }
            CompositionLocalProvider(LocalLook provides lk) {
                WeatherScreen(
                    state = state,
                    onRefresh = { vm.refresh(force = true) },
                    onSelect = vm::select,
                    onRemove = vm::removePlace,
                    onAdd = vm::addPlace,
                    onUseLocation = {
                        if (com.peerloom.weatherglass.data.Locator.hasPermission(this)) vm.addCurrentLocation()
                        else askLocation.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
                    },
                    onSearch = vm::search,
                    onSettings = { s ->
                        if (s.alerts && !state.settings.alerts) askNotify.launch(Manifest.permission.POST_NOTIFICATIONS)
                        vm.updateSettings(s)
                    },
                )
            }
        }
    }
}
