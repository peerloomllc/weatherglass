import Foundation

// The same forecast model as the Android app (data/Model.kt). Everything is
// stored in metric (°C, km/h, mm) and converted for display.

struct Place: Codable, Hashable, Identifiable {
    var name: String
    var lat: Double
    var lon: Double
    var region: String = ""
    /// The "My location" entry. Its lat/lon is the last fix while the app was open.
    var isCurrent: Bool = false
    var id: String { isCurrent ? "current" : String(format: "%.3f,%.3f", lat, lon) }
}

struct Current: Codable {
    var time: String
    var tempC: Double
    var feelsC: Double
    var humidity: Int
    var windKmh: Double
    var windDir: Int
    var code: Int
    var isDay: Bool
}

struct Hour: Codable {
    var time: String // local ISO, e.g. 2026-11-25T14:00
    var tempC: Double
    var rainChance: Int
    var rainMm: Double
    var code: Int
    var isDay: Bool
}

struct Day: Codable {
    var date: String // 2026-11-25
    var code: Int
    var maxC: Double
    var minC: Double
    var rainChance: Int
    var sunrise: String
    var sunset: String
    var uvMax: Double
    var sunHours: Double = 0
}

struct Quarter: Codable {
    var time: String
    var rainMm: Double
}

struct Alert: Codable, Identifiable {
    var id: String
    var event: String
    var headline: String
    var severity: String
    var ends: String?
    var description: String = ""
}

struct Forecast: Codable {
    var place: Place
    var fetchedAt: Double // epoch millis, as on Android
    var utcOffsetSeconds: Int
    var current: Current
    var hours: [Hour]
    var days: [Day]
    var quarters: [Quarter]
    var alerts: [Alert] = []
}

enum TempUnit: String, Codable, CaseIterable { case F, C }
enum WindUnit: String, Codable, CaseIterable {
    case MPH, KMH, MS
    var label: String { switch self { case .MPH: "mph"; case .KMH: "km/h"; case .MS: "m/s" } }
}

struct Settings: Codable, Equatable {
    var tempUnit: TempUnit
    var windUnit: WindUnit
    var use24h: Bool
    var skin: String = "mono"
    var alerts: Bool = true

    static var defaults: Settings {
        let us = ["US", "LR", "MM"].contains(Locale.current.region?.identifier ?? "")
        return Settings(tempUnit: us ? .F : .C, windUnit: us ? .MPH : .KMH, use24h: !us)
    }
}
