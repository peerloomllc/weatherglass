import Foundation

// Settings, places and the last forecast for each place, shared with the
// widgets through the app group.

let appGroup = "group.com.peerloom.weatherglass"

final class Store {
    static let shared = Store()
    let defaults = UserDefaults(suiteName: appGroup) ?? .standard
    private let dir: URL = {
        let base = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroup)
            ?? FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let d = base.appendingPathComponent("forecasts", isDirectory: true)
        try? FileManager.default.createDirectory(at: d, withIntermediateDirectories: true)
        return d
    }()

    var settings: Settings {
        get { decode(Settings.self, "settings") ?? .defaults }
        set { encode(newValue, "settings") }
    }

    var places: [Place] {
        get { decode([Place].self, "places") ?? [] }
        set { encode(newValue, "places") }
    }

    var selected: Int {
        get { defaults.integer(forKey: "selected") }
        set { defaults.set(newValue, forKey: "selected") }
    }

    func selectedPlace() -> Place? { let p = places; return p[safe: selected] ?? p.first }

    private func file(_ p: Place) -> URL {
        dir.appendingPathComponent(p.isCurrent ? "current.json" : String(format: "%.3f_%.3f.json", p.lat, p.lon))
    }

    func load(_ p: Place) -> Forecast? {
        guard let d = try? Data(contentsOf: file(p)) else { return nil }
        return try? JSONDecoder().decode(Forecast.self, from: d)
    }

    func save(_ f: Forecast) {
        if let d = try? JSONEncoder().encode(f) { try? d.write(to: file(f.place), options: .atomic) }
    }

    func drop(_ p: Place) { try? FileManager.default.removeItem(at: file(p)) }

    /// Download a fresh forecast (and US alerts) and save it.
    func refresh(_ p: Place) async throws -> Forecast {
        var f = try await OpenMeteo.fetch(p)
        if settings.alerts { f.alerts = await Nws.fetch(p.lat, p.lon) }
        save(f)
        return f
    }

    /// The saved forecast if it is younger than maxAge seconds, otherwise a fresh one.
    func refreshIfStale(_ p: Place, maxAge: TimeInterval) async -> Forecast? {
        let cached = load(p)
        if let c = cached, Date().timeIntervalSince1970 * 1000 - c.fetchedAt < maxAge * 1000 { return c }
        return (try? await refresh(p)) ?? cached
    }

    private func decode<T: Decodable>(_ t: T.Type, _ key: String) -> T? {
        defaults.data(forKey: key).flatMap { try? JSONDecoder().decode(t, from: $0) }
    }

    private func encode<T: Encodable>(_ v: T, _ key: String) {
        if let d = try? JSONEncoder().encode(v) { defaults.set(d, forKey: key) }
    }
}
