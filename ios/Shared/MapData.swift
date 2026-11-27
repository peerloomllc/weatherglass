import Foundation

// The map's weather and outlines, as on Android (data/MapGrid.kt and
// ui/Basemap.kt): rain for 12 hours and sunshine for 3 days on a 13 x 13
// grid of points around a place, in one Open-Meteo request that is kept for
// 30 minutes, drawn over built-in Natural Earth outlines (basemap.bin, the
// Android app's own file).

struct MapGrid: Codable {
    var lat0, lon0, span: Double
    var n: Int
    var fetchedAt: Double
    var hours: [String]
    var rain: [[Double]] // rain[hour][point], points row by row from the north-west
    var days: [String]
    var sun: [[Double]] // hours of sun: sun[day][point]

    func lat(_ row: Int) -> Double { lat0 + span - 2 * span * Double(row) / Double(n - 1) }
    func lon(_ col: Int) -> Double { lon0 - lonSpan + 2 * lonSpan * Double(col) / Double(n - 1) }
    var lonSpan: Double { span / max(cos(lat0 * .pi / 180), 0.2) }
}

enum MapWeather {
    static let n = 13
    static let span = 2.0

    static func load(_ place: Place) async throws -> MapGrid {
        let file = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("map.json")
        if let d = try? Data(contentsOf: file), let g = try? JSONDecoder().decode(MapGrid.self, from: d),
           g.lat0 == place.lat, g.lon0 == place.lon, Date().timeIntervalSince1970 * 1000 - g.fetchedAt < 30 * 60_000 {
            return g
        }
        var g = MapGrid(lat0: place.lat, lon0: place.lon, span: span, n: n, fetchedAt: 0, hours: [], rain: [], days: [], sun: [])
        let pts = (0..<n).flatMap { r in (0..<n).map { c in (g.lat(r), g.lon(c)) } }
        let url = "https://api.open-meteo.com/v1/forecast?latitude=" + pts.map { String(format: "%.3f", $0.0) }.joined(separator: ",") +
            "&longitude=" + pts.map { String(format: "%.3f", $0.1) }.joined(separator: ",") +
            "&hourly=precipitation&daily=sunshine_duration&forecast_hours=12&forecast_days=3&timezone=auto"
        let r = try JSONDecoder().decode([Point].self, from: try await Net.get(url))
        guard let first = r.first else { throw URLError(.badServerResponse) }
        g.fetchedAt = Date().timeIntervalSince1970 * 1000
        g.hours = first.hourly.time
        g.rain = first.hourly.time.indices.map { h in r.map { ($0.hourly.precipitation[safe: h] ?? nil) ?? 0 } }
        g.days = first.daily.time
        g.sun = first.daily.time.indices.map { d in r.map { (($0.daily.sunshine_duration[safe: d] ?? nil) ?? 0) / 3600 } }
        if let d = try? JSONEncoder().encode(g) { try? d.write(to: file) }
        return g
    }

    private struct Point: Decodable { var hourly: Hourly; var daily: Daily }
    private struct Hourly: Decodable { var time: [String]; var precipitation: [Double?] }
    private struct Daily: Decodable { var time: [String]; var sunshine_duration: [Double?] }
}

struct Basemap {
    struct City { var lon, lat: Float; var pop: Int; var name: String }
    var coast, borders, states, lakes: [[Float]]
    var cities: [City]

    static let shared: Basemap? = {
        guard let url = Bundle.main.url(forResource: "basemap", withExtension: "bin"), let d = try? Data(contentsOf: url) else { return nil }
        return read(d)
    }()

    static func read(_ d: Data) -> Basemap? {
        guard d.count > 4, String(data: d.prefix(4), encoding: .ascii) == "WGM1" else { return nil }
        var i = 4
        func u32() -> Int { let v = d.subdata(in: i..<i + 4).withUnsafeBytes { $0.loadUnaligned(as: UInt32.self) }; i += 4; return Int(UInt32(littleEndian: v)) }
        func u16() -> Int { let v = d.subdata(in: i..<i + 2).withUnsafeBytes { $0.loadUnaligned(as: UInt16.self) }; i += 2; return Int(UInt16(littleEndian: v)) }
        func f32() -> Float { let v = d.subdata(in: i..<i + 4).withUnsafeBytes { $0.loadUnaligned(as: UInt32.self) }; i += 4; return Float(bitPattern: UInt32(littleEndian: v)) }
        func layer() -> [[Float]] { (0..<u32()).map { _ in let n = u16(); return (0..<n * 2).map { _ in f32() } } }
        let coast = layer(), borders = layer(), states = layer(), lakes = layer()
        let cities = (0..<u32()).map { _ -> City in
            let lon = f32(), lat = f32(), pop = u32()
            let len = Int(d[i]); i += 1
            let name = String(data: d.subdata(in: i..<i + len), encoding: .utf8) ?? ""
            i += len
            return City(lon: lon, lat: lat, pop: pop, name: name)
        }
        return Basemap(coast: coast, borders: borders, states: states, lakes: lakes, cities: cities)
    }
}
