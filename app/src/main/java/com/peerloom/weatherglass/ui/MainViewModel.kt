package com.peerloom.weatherglass.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.peerloom.weatherglass.data.Forecast
import com.peerloom.weatherglass.data.Locator
import com.peerloom.weatherglass.data.OpenMeteo
import com.peerloom.weatherglass.data.Place
import com.peerloom.weatherglass.data.Repo
import com.peerloom.weatherglass.data.Settings
import com.peerloom.weatherglass.widget.Widgets
import com.peerloom.weatherglass.work.RefreshWorker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class UiState(
    val places: List<Place> = emptyList(),
    val selected: Int = 0,
    val forecast: Forecast? = null,
    val refreshing: Boolean = false,
    val error: String? = null,
    val settings: Settings,
    val searchResults: List<Place> = emptyList(),
    val searching: Boolean = false,
)

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val repo = Repo(app)
    private val prefs = repo.prefs

    private val _state = MutableStateFlow(UiState(settings = prefs.settings))
    val state: StateFlow<UiState> = _state

    init {
        val places = prefs.places
        val sel = prefs.selected.coerceIn(0, (places.size - 1).coerceAtLeast(0))
        _state.update { it.copy(places = places, selected = sel, forecast = places.getOrNull(sel)?.let(repo.cache::load)) }
        RefreshWorker.schedule(app)
    }

    private val place get() = _state.value.places.getOrNull(_state.value.selected)

    // Called on open and on pull-to-refresh. A forecast under 10 minutes old
    // is kept unless the user pulled to refresh.
    fun refresh(force: Boolean = false) {
        val p = place ?: return
        if (_state.value.refreshing) return
        val cached = _state.value.forecast
        if (!force && cached != null && cached.place == p && System.currentTimeMillis() - cached.fetchedAt < 10 * 60_000) return
        _state.update { it.copy(refreshing = true, error = null) }
        viewModelScope.launch {
            try {
                var target = p
                if (p.isCurrent) {
                    Locator.locate(getApplication())?.let { loc ->
                        target = p.copy(lat = loc.latitude, lon = loc.longitude)
                        replacePlace(p, target)
                    }
                }
                val f = repo.refresh(target)
                // Alerts shown on screen count as seen, so the hourly check
                // does not send a notification for them later.
                prefs.seenAlerts = prefs.seenAlerts + f.alerts.map { it.id }
                _state.update { if (it.places.getOrNull(it.selected) == target) it.copy(forecast = f) else it }
                Widgets.updateAll(getApplication())
            } catch (e: Exception) {
                _state.update { it.copy(error = "Could not update. Showing the last forecast.") }
            } finally {
                _state.update { it.copy(refreshing = false) }
            }
        }
    }

    private fun replacePlace(old: Place, new: Place) {
        val list = _state.value.places.map { if (it == old) new else it }
        prefs.places = list
        _state.update { it.copy(places = list) }
    }

    fun select(i: Int) {
        prefs.selected = i
        val p = _state.value.places.getOrNull(i)
        _state.update { it.copy(selected = i, forecast = p?.let(repo.cache::load), error = null) }
        refresh()
        viewModelScope.launch { Widgets.updateAll(getApplication()) }
    }

    fun addPlace(p: Place) {
        val list = _state.value.places
        val existing = list.indexOfFirst { if (p.isCurrent) it.isCurrent else !it.isCurrent && it.lat == p.lat && it.lon == p.lon }
        if (existing >= 0) { select(existing); return }
        // My location always sits first.
        val newList = if (p.isCurrent) listOf(p) + list else list + p
        prefs.places = newList
        _state.update { it.copy(places = newList, searchResults = emptyList()) }
        select(newList.indexOf(p))
    }

    fun addCurrentLocation() = addPlace(Place("My location", 0.0, 0.0, isCurrent = true))

    fun removePlace(i: Int) {
        val list = _state.value.places
        val p = list.getOrNull(i) ?: return
        repo.cache.drop(p)
        val newList = list.filterIndexed { idx, _ -> idx != i }
        prefs.places = newList
        val sel = _state.value.selected.let { if (it >= i) (it - 1).coerceAtLeast(0) else it }
        _state.update { it.copy(places = newList) }
        select(sel)
    }

    private var searchJob: Job? = null
    fun search(q: String) {
        searchJob?.cancel()
        if (q.trim().length < 2) { _state.update { it.copy(searchResults = emptyList(), searching = false) }; return }
        searchJob = viewModelScope.launch {
            delay(350)
            _state.update { it.copy(searching = true) }
            val r = withContext(Dispatchers.IO) { runCatching { OpenMeteo.search(q) }.getOrDefault(emptyList()) }
            _state.update { it.copy(searchResults = r, searching = false) }
        }
    }

    fun updateSettings(s: Settings) {
        val old = _state.value.settings
        val alertsTurnedOn = s.alerts && !old.alerts
        prefs.settings = s
        if (s.rainSoonAlert != old.rainSoonAlert) RefreshWorker.schedule(getApplication())
        _state.update { it.copy(settings = s) }
        viewModelScope.launch { Widgets.updateAll(getApplication()) }
        if (alertsTurnedOn) refresh(force = true)
    }
}
