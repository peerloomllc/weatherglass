import SwiftUI
import UIKit

// A skin is the colors, type and pictures shared by the app and the widgets.
// The list comes from skins.json, written from the Android app's Skin.kt by
// tools/skins_json.py. Pictures are the Android app's own files
// (app/src/main/res/drawable-nodpi), copied into the app as they are.

struct Palette: Decodable {
    var bgTop, bgBottom, card, text, subtle, accent, icon, alert, alertMild, alertText, alertMildText: String
}

enum SkinFont: String, Decodable { case sans, serif, mono }

struct Skin: Decodable, Identifiable, Equatable {
    var id: String
    var name: String
    var light: Palette
    var dark: Palette
    var font: SkinFont
    var corner: Int
    var upperLabels: Bool
    var followsSystem: Bool
    var miniBelow: Int

    func palette(dark isDark: Bool) -> Palette { followsSystem && isDark ? dark : light }
    static func == (a: Skin, b: Skin) -> Bool { a.id == b.id }
}

struct SkinGroup: Decodable { var name: String; var skins: [String] }

enum Skins {
    private struct File: Decodable { var skins: [Skin]; var groups: [SkinGroup] }

    /// The app's own bundle, also when running inside the widget extension
    /// (which sits in the app's PlugIns folder), so the art ships once.
    static let appBundle: Bundle = {
        let url = Bundle.main.bundleURL
        if url.pathExtension == "appex" {
            return Bundle(url: url.deletingLastPathComponent().deletingLastPathComponent()) ?? .main
        }
        return .main
    }()

    private static let file: File = {
        guard let url = appBundle.url(forResource: "skins", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let f = try? JSONDecoder().decode(File.self, from: data) else { return File(skins: [], groups: []) }
        return f
    }()

    static var all: [Skin] { file.skins }
    static var groups: [(String, [Skin])] { file.groups.map { g in (g.name, g.skins.compactMap { id in all.first { $0.id == id } }) } }
    /// The skin setting's value for "a different skin every day".
    static let daily = "daily"

    /// The skin to show for a skin setting: `daily` gives today's pick.
    static func byId(_ id: String?, today: Date = Date()) -> Skin {
        id == daily ? dailyPick(today) : (all.first { $0.id == id } ?? all[0])
    }

    /// Today's skin for the daily setting: every skin once in a shuffled
    /// order before any repeats, never the same skin two days running.
    static func dailyPick(_ date: Date) -> Skin {
        let n = all.count
        guard n > 1 else { return all[0] }
        let day = Int(floor(date.timeIntervalSince1970 / 86400 + Double(TimeZone.current.secondsFromGMT(for: date)) / 86400))
        let round = Int(floor(Double(day) / Double(n)))
        let i = ((day % n) + n) % n
        let order = shuffled(round)
        let prevLast = shuffled(round - 1).last!
        if i == 0 && order[0] == prevLast { return order[1] }
        if i == 1 && order[0] == prevLast { return order[0] }
        return order[i]
    }

    private static func shuffled(_ round: Int) -> [Skin] {
        var rng = SplitMix(seed: UInt64(bitPattern: Int64(round)))
        return all.shuffled(using: &rng)
    }

    // The Android folder is copied in under its own name.
    private static let artDir = appBundle.resourceURL?.appendingPathComponent("drawable-nodpi")
    private static var cache = NSCache<NSString, UIImage>()

    /// The skin's own picture for this weather, or nil if it uses the plain
    /// symbols. Night falls back to day, small sizes use the "_mini" set.
    static func art(_ skin: Skin, code: Int, isDay: Bool, small: Bool = false) -> UIImage? {
        let base = "skin_\(skin.id)_\(condition(code).rawValue)"
        var names: [String] = []
        for suffix in small ? ["_mini", ""] : [""] {
            if !isDay { names.append("\(base)_night\(suffix)") }
            names.append("\(base)_day\(suffix)")
        }
        for n in names {
            if let img = cache.object(forKey: n as NSString) { return img }
            if let url = artDir?.appendingPathComponent(n + ".webp"), let img = UIImage(contentsOfFile: url.path) {
                cache.setObject(img, forKey: n as NSString)
                return img
            }
        }
        return nil
    }

    /// SF Symbol for skins without their own pictures (Minimal Mono).
    static func symbol(code: Int, isDay: Bool) -> String {
        switch condition(code) {
        case .clear: isDay ? "sun.max" : "moon.stars"
        case .partly: isDay ? "cloud.sun" : "cloud.moon"
        case .cloudy: "cloud"
        case .fog: "cloud.fog"
        case .drizzle: "cloud.drizzle"
        case .rain: "cloud.rain"
        case .sleet: "cloud.sleet"
        case .snow: "cloud.snow"
        case .thunder: "cloud.bolt.rain"
        }
    }
}

extension Color {
    /// "#AARRGGBB", as written by tools/skins_json.py.
    init(argb: String) {
        let v = UInt32(argb.dropFirst(), radix: 16) ?? 0xFF000000
        self.init(.sRGB, red: Double((v >> 16) & 0xFF) / 255, green: Double((v >> 8) & 0xFF) / 255,
                  blue: Double(v & 0xFF) / 255, opacity: Double((v >> 24) & 0xFF) / 255)
    }
}

/// A skin's resolved colors and type, handed down the view tree.
struct Look {
    var skin: Skin
    var p: Palette
    var bgTop: Color { Color(argb: p.bgTop) }
    var bgBottom: Color { Color(argb: p.bgBottom) }
    var card: Color { Color(argb: p.card) }
    var text: Color { Color(argb: p.text) }
    var subtle: Color { Color(argb: p.subtle) }
    var accent: Color { Color(argb: p.accent) }
    var icon: Color { Color(argb: p.icon) }
    var alert: Color { Color(argb: p.alert) }
    var alertMild: Color { Color(argb: p.alertMild) }
    var alertText: Color { Color(argb: p.alertText) }
    var alertMildText: Color { Color(argb: p.alertMildText) }
    var corner: CGFloat { CGFloat(skin.corner) }

    func label(_ s: String) -> String { skin.upperLabels ? s.uppercased() : s }

    func font(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        let design: Font.Design = switch skin.font { case .sans: .default; case .serif: .serif; case .mono: .monospaced }
        return .system(size: size, weight: weight, design: design)
    }

    static func current(_ settings: Settings, dark: Bool) -> Look {
        let s = Skins.byId(settings.skin)
        return Look(skin: s, p: s.palette(dark: dark))
    }
}

private struct LookKey: EnvironmentKey {
    static let defaultValue = Look(skin: Skins.all.first!, p: Skins.all.first!.light)
}

extension EnvironmentValues {
    var look: Look {
        get { self[LookKey.self] }
        set { self[LookKey.self] = newValue }
    }
}

/// The weather picture in the skin's style: its own art, or a tinted symbol.
struct WeatherIcon: View {
    @Environment(\.look) var look
    var code: Int
    var isDay: Bool
    var size: CGFloat

    var body: some View {
        if let img = Skins.art(look.skin, code: code, isDay: isDay, small: size < CGFloat(look.skin.miniBelow)) {
            Image(uiImage: img).resizable().interpolation(["pixel", "teletext", "rpg"].contains(look.skin.id) ? .none : .high)
                .scaledToFit().frame(width: size, height: size)
                .accessibilityLabel(conditionLabel(code, isDay: isDay))
        } else {
            Image(systemName: Skins.symbol(code: code, isDay: isDay)).resizable().scaledToFit()
                .font(.system(size: size, weight: .light)).foregroundStyle(look.icon)
                .frame(width: size * 0.86, height: size * 0.86).frame(width: size, height: size)
                .accessibilityLabel(conditionLabel(code, isDay: isDay))
        }
    }
}

/// A small seeded random generator, so every widget and screen picks the same skin all day.
struct SplitMix: RandomNumberGenerator {
    var state: UInt64
    init(seed: UInt64) { state = seed &+ 0x9E3779B97F4A7C15 }
    mutating func next() -> UInt64 {
        state = state &+ 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
}
