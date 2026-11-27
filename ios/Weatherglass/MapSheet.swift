import SwiftUI
import UIKit

// The map: rain for the next 12 hours or sunshine for the next 3 days,
// colored over built-in coastlines, borders and city names around the place.

private enum Layer { case rain, sun }

// Value it starts at, color, legend label (as on Android).
private let rainSteps: [(Double, UIColor, String)] = [
    (0.1, UIColor(rgb: 0x9BD3FF), "0.1"), (0.5, UIColor(rgb: 0x4EA8F5), "0.5"), (2, UIColor(rgb: 0x2364D9), "2"),
    (5, UIColor(rgb: 0x7B3FE4), "5"), (10, UIColor(rgb: 0xD23CC0), "10+"),
]
private let sunSteps: [(Double, UIColor, String)] = [
    (0, UIColor(rgb: 0x8D99AE), "0"), (2, UIColor(rgb: 0xE9D98B), "2"), (4, UIColor(rgb: 0xFFD23F), "4"),
    (6, UIColor(rgb: 0xFFA62B), "6"), (8, UIColor(rgb: 0xF46A1F), "8+"),
]

struct MapSheet: View {
    @Environment(\.look) var look
    @Environment(\.dismiss) var dismiss
    var place: Place
    var settings: Settings
    /// The place's offset from UTC, so "Today" is the place's today.
    var utcOffset: Int
    @State private var grid: MapGrid?
    @State private var failed = false
    @State private var layer = Layer.rain
    @State private var hour = 0.0
    @State private var day = 0

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Picker("", selection: $layer) { Text("Rain").tag(Layer.rain); Text("Sunshine").tag(Layer.sun) }.pickerStyle(.segmented)
                    ZStack {
                        RoundedRectangle(cornerRadius: min(look.corner, 16)).fill(look.card)
                        if let g = grid {
                            MapCanvas(g: g, layer: layer, index: layer == .rain ? Int(hour) : day)
                        } else {
                            T(failed ? "Couldn't load the map. Check your connection." : "Loading…", 14, color: look.subtle)
                        }
                    }
                    .aspectRatio(1, contentMode: .fit)
                    .clipShape(RoundedRectangle(cornerRadius: min(look.corner, 16)))
                    if let g = grid {
                        if layer == .rain, g.hours.count > 1 {
                            let i = min(Int(hour), g.hours.count - 1)
                            T(i == 0 ? "Now" : hourLabel(g.hours[i], use24h: settings.use24h), 15, .medium)
                            Slider(value: $hour, in: 0...Double(g.hours.count - 1), step: 1)
                            Legend(steps: rainSteps, what: "mm of rain per hour")
                        } else if layer == .sun, !g.days.isEmpty {
                            Picker("", selection: $day) {
                                ForEach(g.days.indices, id: \.self) { Text(dayLabel(g.days[$0], today: placeNow(utcOffset))).tag($0) }
                            }.pickerStyle(.segmented)
                            Legend(steps: sunSteps, what: "hours of sunshine")
                        }
                    }
                    T("Forecast by Open-Meteo, not live radar. Map data: Natural Earth.", 12, color: look.subtle)
                }
                .padding(20)
            }
            .background(look.bgTop)
            .navigationTitle(look.label("Map"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .task {
                do { grid = try await MapWeather.load(place) } catch { failed = true }
            }
        }
    }
}

private struct Legend: View {
    @Environment(\.look) var look
    var steps: [(Double, UIColor, String)]
    var what: String
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 10) {
                ForEach(steps, id: \.2) { _, c, label in
                    HStack(spacing: 4) {
                        RoundedRectangle(cornerRadius: 3).fill(Color(c).opacity(0.8)).frame(width: 12, height: 12)
                        T(label, 12, color: look.subtle)
                    }
                }
            }
            T(what, 12, color: look.subtle)
        }
    }
}

private struct MapCanvas: View {
    @Environment(\.look) var look
    var g: MapGrid
    var layer: Layer
    var index: Int

    var body: some View {
        let values = (layer == .rain ? g.rain : g.sun)[safe: index] ?? []
        let image = smooth(values, n: g.n, steps: layer == .rain ? rainSteps : sunSteps)
        Canvas { ctx, size in
            let w = size.width
            func px(_ lon: Float) -> CGFloat { CGFloat((Double(lon) - g.lon0) / g.lonSpan + 1) / 2 * w }
            func py(_ lat: Float) -> CGFloat { CGFloat((g.lat0 - Double(lat)) / g.span + 1) / 2 * w }
            if let image { ctx.draw(Image(uiImage: image).interpolation(.high), in: CGRect(x: 0, y: 0, width: w, height: w)) }
            guard let base = Basemap.shared else { return }
            func outlines(_ lines: [[Float]], _ color: Color, _ width: CGFloat, dash: [CGFloat] = []) {
                var path = Path()
                for l in lines {
                    var on = false
                    for k in stride(from: 0, to: l.count - 1, by: 2) {
                        let p = CGPoint(x: px(l[k]), y: py(l[k + 1]))
                        let inside = p.x > -w && p.x < 2 * w && p.y > -w && p.y < 2 * w
                        if inside && on { path.addLine(to: p) } else if inside { path.move(to: p); on = true } else { on = false }
                    }
                }
                ctx.stroke(path, with: .color(color), style: StrokeStyle(lineWidth: width, dash: dash))
            }
            outlines(base.states, look.subtle.opacity(0.45), 0.8, dash: [3, 3])
            outlines(base.borders, look.text.opacity(0.6), 1.3)
            outlines(base.coast, look.text.opacity(0.75), 1.4)
            outlines(base.lakes, look.text.opacity(0.55), 1)
            // The biggest cities in view, spaced apart.
            var placed = [CGPoint(x: w / 2, y: w / 2)]
            for c in base.cities {
                if placed.count > 9 { break }
                let p = CGPoint(x: px(c.lon), y: py(c.lat))
                if p.x < 12 || p.y < 12 || p.x > w - 12 || p.y > w - 12 { continue }
                if placed.contains(where: { hypot($0.x - p.x, $0.y - p.y) < 56 }) { continue }
                placed.append(p)
                ctx.fill(Path(ellipseIn: CGRect(x: p.x - 2.5, y: p.y - 2.5, width: 5, height: 5)), with: .color(look.text.opacity(0.8)))
                let label = ctx.resolve(Text(c.name).font(.system(size: 11)).foregroundStyle(look.text))
                let sz = label.measure(in: size)
                let x = min(max(p.x, sz.width / 2 + 2), w - sz.width / 2 - 2)
                var shadow = ctx
                shadow.addFilter(.shadow(color: look.card, radius: 3))
                shadow.draw(label, at: CGPoint(x: x, y: p.y + 4 + sz.height / 2))
            }
            // The place itself.
            ctx.fill(Path(ellipseIn: CGRect(x: w / 2 - 8, y: w / 2 - 8, width: 16, height: 16)), with: .color(look.card))
            ctx.fill(Path(ellipseIn: CGRect(x: w / 2 - 6, y: w / 2 - 6, width: 12, height: 12)), with: .color(look.accent))
        }
    }
}

/// The grid as a small picture, blended smoothly between points and between
/// the legend's colors, fading out below the first step.
private func smooth(_ values: [Double], n: Int, steps: [(Double, UIColor, String)]) -> UIImage? {
    guard values.count >= n * n else { return nil }
    let size = 128
    var px = [UInt8](repeating: 0, count: size * size * 4)
    for y in 0..<size {
        for x in 0..<size {
            let gx = Double(x) * Double(n - 1) / Double(size - 1), gy = Double(y) * Double(n - 1) / Double(size - 1)
            let c0 = min(Int(gx), n - 2), r0 = min(Int(gy), n - 2)
            let fx = gx - Double(c0), fy = gy - Double(r0)
            func at(_ r: Int, _ c: Int) -> Double { values[r * n + c] }
            let v = at(r0, c0) * (1 - fx) * (1 - fy) + at(r0, c0 + 1) * fx * (1 - fy) + at(r0 + 1, c0) * (1 - fx) * fy + at(r0 + 1, c0 + 1) * fx * fy
            let (r, g, b, a) = shade(v, steps)
            let o = (y * size + x) * 4
            // Premultiplied RGBA.
            px[o] = UInt8(r * a * 255); px[o + 1] = UInt8(g * a * 255); px[o + 2] = UInt8(b * a * 255); px[o + 3] = UInt8(a * 255)
        }
    }
    guard let provider = CGDataProvider(data: Data(px) as CFData),
          let cg = CGImage(width: size, height: size, bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: size * 4,
                           space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue),
                           provider: provider, decode: nil, shouldInterpolate: true, intent: .defaultIntent) else { return nil }
    return UIImage(cgImage: cg)
}

private func shade(_ v: Double, _ steps: [(Double, UIColor, String)]) -> (Double, Double, Double, Double) {
    func rgb(_ c: UIColor) -> (Double, Double, Double) {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        c.getRed(&r, green: &g, blue: &b, alpha: &a)
        return (Double(r), Double(g), Double(b))
    }
    let alpha = 0.6
    let first = steps[0]
    if v < first.0 * 0.5 { return (0, 0, 0, 0) }
    if v < first.0 {
        let c = rgb(first.1)
        return (c.0, c.1, c.2, alpha * (v - first.0 * 0.5) / (first.0 * 0.5))
    }
    if v >= steps.last!.0 { let c = rgb(steps.last!.1); return (c.0, c.1, c.2, alpha) }
    let i = steps.lastIndex { v >= $0.0 }!
    let a = steps[i], b = steps[i + 1]
    let t = (v - a.0) / (b.0 - a.0)
    let ca = rgb(a.1), cb = rgb(b.1)
    return (ca.0 + (cb.0 - ca.0) * t, ca.1 + (cb.1 - ca.1) * t, ca.2 + (cb.2 - ca.2) * t, alpha)
}

extension UIColor {
    convenience init(rgb: UInt32) {
        self.init(red: CGFloat((rgb >> 16) & 0xFF) / 255, green: CGFloat((rgb >> 8) & 0xFF) / 255, blue: CGFloat(rgb & 0xFF) / 255, alpha: 1)
    }
}
