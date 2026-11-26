import SwiftUI
import WidgetKit

// Home screen and lock screen widgets. They read the forecast the app saved
// in the app group, download a new one if it is over 20 minutes old, and ask
// iOS to come back in 30 minutes (iOS decides when it really does).

struct WeatherEntry: TimelineEntry {
    let date: Date
    let forecast: Forecast?
    let settings: Settings
}

struct Provider: TimelineProvider {
    func placeholder(in context: Context) -> WeatherEntry {
        WeatherEntry(date: Date(), forecast: nil, settings: Store.shared.settings)
    }

    func getSnapshot(in context: Context, completion: @escaping (WeatherEntry) -> Void) {
        let s = Store.shared
        completion(WeatherEntry(date: Date(), forecast: s.selectedPlace().flatMap { s.load($0) }, settings: s.settings))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<WeatherEntry>) -> Void) {
        Task {
            let s = Store.shared
            var f: Forecast?
            if let p = s.selectedPlace(), !(p.isCurrent && p.lat == 0 && p.lon == 0) {
                f = await s.refreshIfStale(p, maxAge: 20 * 60)
            }
            let entry = WeatherEntry(date: Date(), forecast: f, settings: s.settings)
            completion(Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(30 * 60))))
        }
    }
}

struct WidgetView: View {
    @Environment(\.widgetFamily) var family
    @Environment(\.colorScheme) var scheme
    var entry: WeatherEntry

    var body: some View {
        let look = Look.current(entry.settings, dark: scheme == .dark)
        Group {
            if let f = entry.forecast {
                switch family {
                case .accessoryInline: Inline(f: f, s: entry.settings)
                case .accessoryCircular: Circular(f: f, s: entry.settings)
                case .accessoryRectangular: Rectangular(f: f, s: entry.settings)
                case .systemSmall: Small(f: f, s: entry.settings)
                case .systemMedium: Medium(f: f, s: entry.settings)
                default: Large(f: f, s: entry.settings)
                }
            } else {
                Text("Open Weatherglass").font(look.font(13)).foregroundStyle(look.subtle)
            }
        }
        .environment(\.look, look)
        .containerBackground(for: .widget) {
            LinearGradient(colors: [look.bgTop, look.bgBottom], startPoint: .top, endPoint: .bottom)
        }
    }
}

private struct Small: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        let c = f.current
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                T(f.place.name, 13, .medium).lineLimit(1)
                Spacer(minLength: 0)
            }
            HStack(alignment: .center) {
                T(tempText(c.tempC, s.tempUnit), 40, .light)
                Spacer(minLength: 0)
                WeatherIcon(code: c.code, isDay: c.isDay, size: 48)
            }
            Spacer(minLength: 0)
            T(look.label(conditionLabel(c.code, isDay: c.isDay)), 13, color: look.subtle).lineLimit(1)
            if let d = f.days.first { T("H \(tempText(d.maxC, s.tempUnit))  L \(tempText(d.minC, s.tempUnit))", 13, color: look.subtle) }
        }
    }
}

private struct Medium: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        VStack(spacing: 8) {
            HStack(alignment: .top) {
                Small(f: f, s: s).frame(maxWidth: 140)
                Spacer(minLength: 8)
                NextHours(f: f, s: s, count: 4)
            }
        }
    }
}

private struct Large: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                Small(f: f, s: s).frame(maxWidth: 150, maxHeight: 120)
                Spacer(minLength: 8)
                NextHours(f: f, s: s, count: 4)
            }
            Divider().overlay(look.subtle.opacity(0.4))
            let today = placeNow(f.utcOffsetSeconds)
            ForEach(f.days.filter { $0.date >= dayString(today) }.prefix(5), id: \.date) { d in
                HStack(spacing: 8) {
                    T(dayLabel(d.date, today: today), 14).frame(width: 84, alignment: .leading).lineLimit(1)
                    WeatherIcon(code: d.code, isDay: true, size: 24)
                    T(d.rainChance >= 20 ? "\(d.rainChance)%" : "", 12, color: look.accent).frame(width: 34, alignment: .leading)
                    Spacer()
                    T(tempText(d.minC, s.tempUnit), 14, color: look.subtle)
                    T(tempText(d.maxC, s.tempUnit), 14, .medium).frame(width: 36, alignment: .trailing)
                }
            }
        }
    }
}

private struct NextHours: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var count: Int
    var body: some View {
        let now = placeNow(f.utcOffsetSeconds)
        let key = dayString(now) + "T" + String(format: "%02d", Calendar(identifier: .gregorian).dateComponents(in: TimeZone(identifier: "UTC")!, from: now).hour ?? 0)
        HStack(spacing: 8) {
            ForEach(Array(f.hours.filter { String($0.time.prefix(13)) > key }.prefix(count).enumerated()), id: \.offset) { _, h in
                VStack(spacing: 4) {
                    T(hourLabel(h.time, use24h: s.use24h), 11, color: look.subtle).lineLimit(1).fixedSize()
                    WeatherIcon(code: h.code, isDay: h.isDay, size: 26)
                    T(tempText(h.tempC, s.tempUnit), 13, .medium).lineLimit(1).fixedSize()
                }
            }
        }
    }
}

// Lock screen: iOS tints these, so they use the plain symbols.

private struct Inline: View {
    var f: Forecast
    var s: Settings
    var body: some View {
        Label("\(tempText(f.current.tempC, s.tempUnit)) \(conditionLabel(f.current.code, isDay: f.current.isDay))",
              systemImage: Skins.symbol(code: f.current.code, isDay: f.current.isDay))
    }
}

private struct Circular: View {
    var f: Forecast
    var s: Settings
    var body: some View {
        ZStack {
            AccessoryWidgetBackground()
            VStack(spacing: 0) {
                Image(systemName: Skins.symbol(code: f.current.code, isDay: f.current.isDay)).font(.system(size: 16))
                Text(tempText(f.current.tempC, s.tempUnit)).font(.system(size: 16, weight: .medium))
            }
        }
    }
}

private struct Rectangular: View {
    var f: Forecast
    var s: Settings
    var body: some View {
        let c = f.current
        VStack(alignment: .leading, spacing: 1) {
            HStack(spacing: 4) {
                Image(systemName: Skins.symbol(code: c.code, isDay: c.isDay))
                Text(tempText(c.tempC, s.tempUnit)).font(.system(size: 17, weight: .semibold))
                Text(f.place.name).font(.system(size: 13)).lineLimit(1)
            }
            Text(conditionLabel(c.code, isDay: c.isDay)).font(.system(size: 13))
            if let d = f.days.first { Text("H \(tempText(d.maxC, s.tempUnit))  L \(tempText(d.minC, s.tempUnit))").font(.system(size: 13)) }
        }
    }
}

struct WeatherWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "Weather", provider: Provider()) { WidgetView(entry: $0) }
            .configurationDisplayName("Weather")
            .description("Now and the coming hours and days, in your skin.")
            .supportedFamilies([.systemSmall, .systemMedium, .systemLarge, .accessoryInline, .accessoryCircular, .accessoryRectangular])
    }
}

@main
struct WeatherglassWidgets: WidgetBundle {
    var body: some Widget { WeatherWidget() }
}
