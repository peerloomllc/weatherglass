import Foundation

// Weather types, units and time labels, matching the Android app.

enum Condition: String {
    case clear, partly, cloudy, fog, drizzle, rain, sleet, snow, thunder

    var label: String {
        switch self {
        case .clear: "Clear"; case .partly: "Partly cloudy"; case .cloudy: "Cloudy"; case .fog: "Fog"
        case .drizzle: "Drizzle"; case .rain: "Rain"; case .sleet: "Freezing rain"; case .snow: "Snow"; case .thunder: "Thunderstorm"
        }
    }
}

/// Open-Meteo's WMO weather codes, folded into the nine types every skin draws.
func condition(_ code: Int) -> Condition {
    switch code {
    case 0, 1: .clear
    case 2: .partly
    case 3: .cloudy
    case 45, 48: .fog
    case 51, 53, 55: .drizzle
    case 56, 57, 66, 67: .sleet
    case 61, 63, 65, 80, 81, 82: .rain
    case 71, 73, 75, 77, 85, 86: .snow
    case 95, 96, 99: .thunder
    default: .cloudy
    }
}

func conditionLabel(_ code: Int, isDay: Bool) -> String {
    let c = condition(code)
    if c == .clear && code == 1 { return isDay ? "Mostly sunny" : "Mostly clear" }
    if c == .clear { return isDay ? "Sunny" : "Clear" }
    return c.label
}

func temp(_ c: Double, _ unit: TempUnit) -> Int { Int((unit == .F ? c * 9 / 5 + 32 : c).rounded()) }
func tempText(_ c: Double, _ unit: TempUnit) -> String { "\(temp(c, unit))°" }

func windText(_ kmh: Double, _ unit: WindUnit) -> String {
    switch unit {
    case .MPH: "\(Int((kmh / 1.609344).rounded())) mph"
    case .KMH: "\(Int(kmh.rounded())) km/h"
    case .MS: "\(Int((kmh / 3.6).rounded())) m/s"
    }
}

func rainText(_ mm: Double, _ unit: TempUnit) -> String {
    unit == .F ? String(format: "%.2f in", mm / 25.4) : String(format: "%.1f mm", mm)
}

func compass(_ deg: Int) -> String {
    ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][(((deg % 360) + 360) % 360 + 22) / 45 % 8]
}

func uvWord(_ uv: Double) -> String {
    switch uv { case ..<3: "Low"; case ..<6: "Moderate"; case ..<8: "High"; case ..<11: "Very high"; default: "Extreme" }
}

/// Hours of sun rounded to the nearest half hour: "7h", "7.5h".
func sunHoursShort(_ h: Double) -> String {
    let r = (h * 2).rounded() / 2
    return r.truncatingRemainder(dividingBy: 1) == 0 ? "\(Int(r))h" : "\(r)h"
}

// Open-Meteo times are local to the place ("2026-11-26T14:00"), so they are
// read as plain dates in UTC and never shifted to the phone's time zone.

private let isoLocal: DateFormatter = {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.timeZone = TimeZone(identifier: "UTC")
    f.dateFormat = "yyyy-MM-dd'T'HH:mm"
    return f
}()

private let isoDay: DateFormatter = {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.timeZone = TimeZone(identifier: "UTC")
    f.dateFormat = "yyyy-MM-dd"
    return f
}()

func parseLocal(_ s: String) -> Date? { isoLocal.date(from: s) }

private var utc: Calendar = {
    var c = Calendar(identifier: .gregorian)
    c.timeZone = TimeZone(identifier: "UTC")!
    return c
}()

func hourLabel(_ s: String, use24h: Bool) -> String {
    guard let d = parseLocal(s) else { return "" }
    let h = utc.component(.hour, from: d)
    if use24h { return String(format: "%02d:00", h) }
    return "\(h % 12 == 0 ? 12 : h % 12)\(h < 12 ? "am" : "pm")"
}

func clockLabel(_ s: String, use24h: Bool) -> String {
    guard let d = parseLocal(s) else { return "" }
    let h = utc.component(.hour, from: d), m = utc.component(.minute, from: d)
    if use24h { return String(format: "%02d:%02d", h, m) }
    return String(format: "%d:%02d %@", h % 12 == 0 ? 12 : h % 12, m, h < 12 ? "AM" : "PM")
}

/// The place's local date and time right now, as a UTC-based Date.
func placeNow(_ utcOffsetSeconds: Int, now: Date = Date()) -> Date { now.addingTimeInterval(Double(utcOffsetSeconds)) }

func dayLabel(_ date: String, today: Date) -> String {
    guard let d = isoDay.date(from: date) else { return date }
    let t = utc.startOfDay(for: today)
    let diff = utc.dateComponents([.day], from: t, to: d).day ?? 0
    if diff == 0 { return "Today" }
    if diff == 1 { return "Tomorrow" }
    let f = DateFormatter()
    f.timeZone = TimeZone(identifier: "UTC")
    f.dateFormat = "EEE"
    return f.string(from: d)
}

func dayString(_ d: Date) -> String { isoDay.string(from: d) }
