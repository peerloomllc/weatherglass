import CoreLocation
import SwiftUI
import WidgetKit

// The app's state: places, settings and the forecast on screen. Refreshes
// when the app comes to the front, skipping the network for a forecast under
// 10 minutes old, and tells the widgets when there is a new one.

@MainActor
final class AppModel: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let store = Store.shared
    @Published var places: [Place] = []
    @Published var selected = 0
    @Published var settings: Settings
    @Published var forecast: Forecast?
    @Published var refreshing = false
    @Published var error: String?
    @Published var results: [Place] = []
    private let location = CLLocationManager()
    private var searchTask: Task<Void, Never>?

    override init() {
        settings = store.settings
        super.init()
        #if DEBUG
        // Testing on the Simulator: launch with -seedPlace "Name,lat,lon" (and
        // optionally -seedSkin id) to start with a place without tapping.
        if let seed = UserDefaults.standard.string(forKey: "seedPlace") {
            let f = seed.split(separator: ",").map(String.init)
            if f.count == 3, let lat = Double(f[1]), let lon = Double(f[2]) {
                store.places = [Place(name: f[0], lat: lat, lon: lon)]
                store.selected = 0
            }
        }
        if let skin = UserDefaults.standard.string(forKey: "seedSkin") {
            var s = store.settings; s.skin = skin; store.settings = s; settings = s
        }
        #endif
        places = store.places
        selected = min(store.selected, max(places.count - 1, 0))
        forecast = store.selectedPlace().flatMap { store.load($0) }
        location.delegate = self
        location.desiredAccuracy = kCLLocationAccuracyKilometer
    }

    var place: Place? { places[safe: selected] ?? places.first }

    func refresh(force: Bool = false) async {
        guard let p = place, !refreshing else { return }
        if p.isCurrent && p.lat == 0 && p.lon == 0 { requestLocation(); return }
        refreshing = true
        defer { refreshing = false }
        do {
            let f: Forecast
            if !force, let c = store.load(p), Date().timeIntervalSince1970 * 1000 - c.fetchedAt < 600_000 { f = c }
            else { f = try await store.refresh(p) }
            if place?.id == p.id { forecast = f }
            error = nil
            WidgetCenter.shared.reloadAllTimelines()
        } catch {
            self.error = "Couldn't update. Showing the last forecast."
        }
    }

    func select(_ i: Int) {
        selected = i
        store.selected = i
        forecast = place.flatMap { store.load($0) }
        Task { await refresh() }
    }

    func add(_ p: Place) {
        if let i = places.firstIndex(where: { $0.id == p.id }) { select(i); return }
        places.append(p)
        store.places = places
        results = []
        select(places.count - 1)
    }

    func remove(_ i: Int) {
        let p = places.remove(at: i)
        store.drop(p)
        store.places = places
        select(min(selected, max(places.count - 1, 0)))
    }

    func addCurrentLocation() {
        if let i = places.firstIndex(where: { $0.isCurrent }) { select(i); requestLocation(); return }
        places.insert(Place(name: "My location", lat: 0, lon: 0, isCurrent: true), at: 0)
        store.places = places
        selected = 0
        store.selected = 0
        forecast = nil
        requestLocation()
    }

    func update(_ s: Settings) {
        let alertsOn = s.alerts && !settings.alerts
        settings = s
        store.settings = s
        WidgetCenter.shared.reloadAllTimelines()
        if alertsOn { Task { await refresh(force: true) } }
    }

    func search(_ q: String) {
        searchTask?.cancel()
        guard q.trimmingCharacters(in: .whitespaces).count >= 2 else { results = []; return }
        searchTask = Task {
            try? await Task.sleep(nanoseconds: 300_000_000)
            if Task.isCancelled { return }
            results = (try? await OpenMeteo.search(q)) ?? []
        }
    }

    // Approximate location only, and only while the app is open.
    private func requestLocation() {
        switch location.authorizationStatus {
        case .notDetermined: location.requestWhenInUseAuthorization()
        case .denied, .restricted: error = "Location is off for Weatherglass. Turn it on in Settings, or pick a city."
        default: location.requestLocation()
        }
    }

    nonisolated func locationManagerDidChangeAuthorization(_ m: CLLocationManager) {
        Task { @MainActor in
            if places.contains(where: { $0.isCurrent }) && [.authorizedWhenInUse, .authorizedAlways].contains(m.authorizationStatus) {
                m.requestLocation()
            }
        }
    }

    nonisolated func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) {
        guard let l = locs.last else { return }
        Task { @MainActor in
            guard let i = places.firstIndex(where: { $0.isCurrent }) else { return }
            // Two decimals (about 1 km) is all the forecast needs.
            let lat = (l.coordinate.latitude * 100).rounded() / 100, lon = (l.coordinate.longitude * 100).rounded() / 100
            places[i].lat = lat
            places[i].lon = lon
            store.places = places
            if selected == i { await refresh(force: true) }
        }
    }

    nonisolated func locationManager(_ m: CLLocationManager, didFailWithError e: Error) {
        Task { @MainActor in error = "Couldn't get your location. Pick a city instead." }
    }
}
