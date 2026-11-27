import SwiftUI

/// Sets the skin's look for everything below, and picks the first screen.
struct RootView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.colorScheme) var scheme

    var body: some View {
        let look = Look.current(model.settings, dark: scheme == .dark)
        ZStack {
            LinearGradient(colors: [look.bgTop, look.bgBottom], startPoint: .top, endPoint: .bottom).ignoresSafeArea()
            if model.places.isEmpty { WelcomeView() } else { ForecastView() }
        }
        .environment(\.look, look)
        .preferredColorScheme(look.bgTop.isDark ? .dark : .light)
        .tint(look.accent)
    }
}

struct WelcomeView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.look) var look
    @State private var picking = false

    var body: some View {
        VStack(spacing: 18) {
            Spacer()
            WeatherIcon(code: 2, isDay: true, size: 120)
            T("Weatherglass", 30, .medium)
            T("Simple weather. No ads, no accounts, no tracking.", 15, color: look.subtle).multilineTextAlignment(.center)
            Spacer()
            Button { model.addCurrentLocation() } label: {
                T("Use my location", 16, .medium, color: look.bgTop).frame(maxWidth: .infinity).padding(14)
                    .background(look.accent, in: RoundedRectangle(cornerRadius: 14))
            }
            Button { picking = true } label: { T("Pick a city", 16, .medium).frame(maxWidth: .infinity).padding(14) }
        }
        .padding(24)
        .sheet(isPresented: $picking) { PlacesSheet() }
    }
}

struct ForecastView: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.look) var look
    @State private var showPlaces = false
    @State private var showSettings = false
    @State private var about: String?? = nil
    @State private var reminder = false

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                HStack {
                    Button { showPlaces = true } label: {
                        HStack(spacing: 6) {
                            if model.place?.isCurrent == true { Image(systemName: "location.fill").foregroundStyle(look.text) }
                            T(model.place?.name ?? "", 20, .medium).lineLimit(1)
                            Image(systemName: "chevron.down").foregroundStyle(look.subtle)
                        }
                    }
                    Spacer()
                    Button { showSettings = true } label: {
                        Image(systemName: "slider.horizontal.3").font(.system(size: 20)).foregroundStyle(look.text).frame(width: 44, height: 44)
                    }.accessibilityLabel("Settings")
                }
                if let f = model.forecast {
                    Now(f: f, s: model.settings, opens: model.opens)
                    ForEach(f.alerts) { AlertBanner(alert: $0) }
                    if let e = model.error { T(e, 13, color: look.subtle) }
                    Hourly(f: f, s: model.settings)
                    Daily(f: f, s: model.settings)
                    Details(f: f, s: model.settings)
                    T("Weather data by Open-Meteo.com (CC BY 4.0)", 12, color: look.subtle).padding(.top, 4)
                } else if let e = model.error {
                    T(e, 15, color: look.subtle).padding(.top, 80)
                } else {
                    ProgressView().padding(.top, 120)
                }
            }
            .padding(.horizontal, 20).padding(.bottom, 32)
        }
        .refreshable { await model.refresh(force: true) }
        .sheet(isPresented: $showPlaces) { PlacesSheet() }
        .sheet(isPresented: $showSettings) { SettingsSheet(onAbout: { showSettings = false; DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { about = .some(nil) } }) }
        .sheet(isPresented: Binding(get: { about != nil }, set: { if !$0 { about = nil } })) {
            AboutSheet(openId: about ?? nil).environment(\.look, look)
        }
        .alert("⚡ Enjoying Weatherglass?", isPresented: $reminder) {
            Button("Donate") { about = .some("support") }
            Button("Maybe later", role: .cancel) {}
            Button("I already donated") {}
        } message: {
            Text("Weatherglass is free, with no ads, accounts or subscriptions. If you get value from it, please consider returning value to support development.")
        }
        .task(id: model.forecast != nil) {
            if model.forecast != nil && DonationReminder.due() { DonationReminder.markShown(); reminder = true }
        }
    }
}

private struct Now: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var opens: Int
    var body: some View {
        let c = f.current
        VStack(spacing: 4) {
            OpeningIcon(code: c.code, isDay: c.isDay, size: 120, playKey: opens, enabled: s.animate)
            // The number is centered; the degree sign hangs off its right side.
            Text("\(temp(c.tempC, s.tempUnit))").font(look.font(84, .light)).foregroundStyle(look.text)
                .overlay(alignment: .topTrailing) { Text("°").font(look.font(84, .light)).foregroundStyle(look.text).offset(x: 34) }
            T(look.label(conditionLabel(c.code, isDay: c.isDay)), 18)
            if let d = f.days.first {
                T("Feels like \(tempText(c.feelsC, s.tempUnit))  ·  H \(tempText(d.maxC, s.tempUnit))  L \(tempText(d.minC, s.tempUnit))", 14, color: look.subtle)
            }
        }
        .frame(maxWidth: .infinity).padding(.vertical, 8)
    }
}

private struct AlertBanner: View {
    @Environment(\.look) var look
    var alert: Alert
    @State private var open = false
    var body: some View {
        let severe = ["Extreme", "Severe"].contains(alert.severity)
        let fg = severe ? look.alertText : look.alertMildText
        VStack(spacing: 8) {
            T(alert.event, 16, .semibold, color: fg).frame(maxWidth: .infinity)
            T(alert.headline, 13, color: fg)
            if open { T(alert.description, 13, color: fg) }
        }
        .padding(14).frame(maxWidth: .infinity)
        .background(severe ? look.alert : look.alertMild, in: RoundedRectangle(cornerRadius: min(look.corner, 16)))
        .onTapGesture { open.toggle() }
    }
}

private struct Hourly: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        let now = dayString(placeNow(f.utcOffsetSeconds)) + "T" + String(format: "%02d", Calendar(identifier: .gregorian).dateComponents(in: TimeZone(identifier: "UTC")!, from: placeNow(f.utcOffsetSeconds)).hour ?? 0)
        let hours = f.hours.filter { String($0.time.prefix(13)) >= now }
        CardBox {
            VStack(alignment: .leading, spacing: 12) {
                T(look.label("Next 48 hours"), 13, color: look.subtle)
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 18) {
                        ForEach(Array(hours.enumerated()), id: \.offset) { i, h in
                            VStack(spacing: 6) {
                                T(i == 0 ? "Now" : hourLabel(h.time, use24h: s.use24h), 13, color: look.subtle)
                                WeatherIcon(code: h.code, isDay: h.isDay, size: 30)
                                T(tempText(h.tempC, s.tempUnit), 16, .medium)
                                T(h.rainChance >= 20 ? "\(h.rainChance)%" : " ", 12, color: look.accent)
                            }
                        }
                    }
                }
            }
        }
    }
}

private struct Daily: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        let today = placeNow(f.utcOffsetSeconds)
        let todayStr = dayString(today)
        let days = f.days.filter { $0.date >= todayStr }
        let lo = days.map { temp($0.minC, s.tempUnit) }.min() ?? 0
        let hi = days.map { temp($0.maxC, s.tempUnit) }.max() ?? 1
        CardBox {
            VStack(alignment: .leading, spacing: 12) {
                T(look.label("Next \(days.count) days"), 13, color: look.subtle)
                ForEach(days, id: \.date) { d in
                    HStack(spacing: 6) {
                        T(dayLabel(d.date, today: today), 16).frame(width: 86, alignment: .leading).lineLimit(1)
                        WeatherIcon(code: d.code, isDay: true, size: 28)
                        Group {
                            if d.rainChance >= 20 { T("\(d.rainChance)%", 12, color: look.accent) }
                            else if d.sunHours >= 0.5 { T("☀" + sunHoursShort(d.sunHours), 12, color: look.subtle) }
                            else { T("", 12) }
                        }.frame(width: 44, alignment: .leading)
                        T(tempText(d.minC, s.tempUnit), 15, color: look.subtle).frame(width: 38, alignment: .leading)
                        RangeBar(lo: lo, hi: hi, min: temp(d.minC, s.tempUnit), max: temp(d.maxC, s.tempUnit))
                        T(tempText(d.maxC, s.tempUnit), 15, .medium).frame(width: 40, alignment: .trailing)
                    }
                }
            }
        }
    }
}

private struct RangeBar: View {
    @Environment(\.look) var look
    var lo, hi, min, max: Int
    var body: some View {
        GeometryReader { g in
            let span = CGFloat(Swift.max(hi - lo, 1))
            let w = g.size.width
            ZStack(alignment: .leading) {
                Capsule().fill(look.subtle.opacity(0.25))
                Capsule().fill(look.accent)
                    .frame(width: Swift.max(w * CGFloat(max - min) / span, 6))
                    .offset(x: w * CGFloat(min - lo) / span)
            }
        }
        .frame(height: 6)
    }
}

private struct Details: View {
    @Environment(\.look) var look
    var f: Forecast
    var s: Settings
    var body: some View {
        let c = f.current
        var cells: [(String, String)] = [("Wind", "\(windText(c.windKmh, s.windUnit)) \(compass(c.windDir))"), ("Humidity", "\(c.humidity)%")]
        if let d = f.days.first {
            let rain = f.hours.filter { $0.time.hasPrefix(d.date) }.reduce(0) { $0 + $1.rainMm }
            cells += [("UV index", "\(Int(d.uvMax.rounded())) \(uvWord(d.uvMax))"), ("Rain today", rainText(rain, s.tempUnit))]
            if !d.sunrise.isEmpty { cells.append(("Sunrise", clockLabel(d.sunrise, use24h: s.use24h))) }
            if !d.sunset.isEmpty { cells.append(("Sunset", clockLabel(d.sunset, use24h: s.use24h))) }
            if let a = parseLocal(d.sunrise), let b = parseLocal(d.sunset) {
                let m = Int(b.timeIntervalSince(a) / 60)
                cells += [("Sunshine", String(sunHoursShort(d.sunHours).dropLast()) + " hours"), ("Daylight", "\(m / 60) h \(m % 60) min")]
            }
        }
        return LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible())], spacing: 14) {
            ForEach(cells, id: \.0) { k, v in
                CardBox {
                    VStack(alignment: .leading, spacing: 4) {
                        T(look.label(k), 13, color: look.subtle)
                        T(v, 18, .medium)
                    }
                }
            }
        }
    }
}

