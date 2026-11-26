import Foundation

// Open-Meteo for forecasts and city search, and the US National Weather
// Service for alerts. Free, no keys. The User-Agent names the app only.

let userAgent = "Weatherglass/0.1 (github.com/peerloomllc/weatherglass)"

enum Net {
    static func get(_ url: String, accept: String = "application/json") async throws -> Data {
        var req = URLRequest(url: URL(string: url)!, timeoutInterval: 15)
        req.setValue(userAgent, forHTTPHeaderField: "User-Agent")
        req.setValue(accept, forHTTPHeaderField: "Accept")
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return data
    }
}

enum OpenMeteo {
    static func forecastUrl(_ lat: Double, _ lon: Double) -> String {
        "https://api.open-meteo.com/v1/forecast?latitude=\(lat)&longitude=\(lon)" +
            "&current=temperature_2m,apparent_temperature,relative_humidity_2m,is_day,weather_code,wind_speed_10m,wind_direction_10m" +
            "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,is_day" +
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max,sunshine_duration" +
            "&minutely_15=precipitation&forecast_days=10&forecast_hours=48&forecast_minutely_15=12&timezone=auto"
    }

    static func fetch(_ place: Place) async throws -> Forecast {
        try parse(try await Net.get(forecastUrl(place.lat, place.lon)), place: place)
    }

    static func parse(_ data: Data, place: Place, now: Date = Date()) throws -> Forecast {
        let r = try JSONDecoder().decode(Resp.self, from: data)
        let c = r.current, h = r.hourly, d = r.daily
        return Forecast(
            place: place,
            fetchedAt: now.timeIntervalSince1970 * 1000,
            utcOffsetSeconds: r.utc_offset_seconds ?? 0,
            current: Current(time: c.time, tempC: c.temperature_2m, feelsC: c.apparent_temperature, humidity: c.relative_humidity_2m,
                             windKmh: c.wind_speed_10m, windDir: c.wind_direction_10m, code: c.weather_code, isDay: c.is_day == 1),
            hours: h.time.indices.map { i in
                Hour(time: h.time[i], tempC: h.temperature_2m[i] ?? 0, rainChance: h.precipitation_probability[i] ?? 0,
                     rainMm: h.precipitation[i] ?? 0, code: h.weather_code[i] ?? 3, isDay: (h.is_day[i] ?? 1) == 1)
            },
            days: d.time.indices.map { i in
                Day(date: d.time[i], code: d.weather_code[i] ?? 3, maxC: d.temperature_2m_max[i] ?? 0, minC: d.temperature_2m_min[i] ?? 0,
                    rainChance: d.precipitation_probability_max[i] ?? 0, sunrise: d.sunrise[i] ?? "", sunset: d.sunset[i] ?? "",
                    uvMax: d.uv_index_max[i] ?? 0, sunHours: ((d.sunshine_duration?[safe: i] ?? nil) ?? 0) / 3600)
            },
            quarters: r.minutely_15.map { m in m.time.indices.map { Quarter(time: m.time[$0], rainMm: m.precipitation[$0] ?? 0) } } ?? []
        )
    }

    static func search(_ query: String) async throws -> [Place] {
        let q = query.trimmingCharacters(in: .whitespaces).addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let data = try await Net.get("https://geocoding-api.open-meteo.com/v1/search?name=\(q)&count=8&format=json")
        let r = try JSONDecoder().decode(GeoResp.self, from: data)
        return (r.results ?? []).map { Place(name: $0.name, lat: $0.latitude, lon: $0.longitude, region: [$0.admin1, $0.country].compactMap { $0 }.joined(separator: ", ")) }
    }

    private struct Resp: Decodable {
        var utc_offset_seconds: Int?
        var current: Cur
        var hourly: Hourly
        var daily: Daily
        var minutely_15: Minutely?
    }
    private struct Cur: Decodable {
        var time: String
        var temperature_2m: Double
        var apparent_temperature: Double
        var relative_humidity_2m: Int
        var is_day: Int
        var weather_code: Int
        var wind_speed_10m: Double
        var wind_direction_10m: Int
    }
    private struct Hourly: Decodable {
        var time: [String]
        var temperature_2m: [Double?]
        var precipitation_probability: [Int?]
        var precipitation: [Double?]
        var weather_code: [Int?]
        var is_day: [Int?]
    }
    private struct Daily: Decodable {
        var time: [String]
        var weather_code: [Int?]
        var temperature_2m_max: [Double?]
        var temperature_2m_min: [Double?]
        var precipitation_probability_max: [Int?]
        var sunrise: [String?]
        var sunset: [String?]
        var uv_index_max: [Double?]
        var sunshine_duration: [Double?]?
    }
    private struct Minutely: Decodable {
        var time: [String]
        var precipitation: [Double?]
    }
    private struct GeoResp: Decodable { var results: [GeoHit]? }
    private struct GeoHit: Decodable {
        var name: String
        var latitude: Double
        var longitude: Double
        var admin1: String?
        var country: String?
    }
}

enum Nws {
    /// Rough box around the US states and Puerto Rico. Places outside it are never sent to the NWS.
    static func covers(_ lat: Double, _ lon: Double) -> Bool { (17.0...72.0).contains(lat) && (-180.0 ... -64.0).contains(lon) }

    static func fetch(_ lat: Double, _ lon: Double) async -> [Alert] {
        guard covers(lat, lon) else { return [] }
        let url = String(format: "https://api.weather.gov/alerts/active?point=%.4f,%.4f", lat, lon)
        guard let data = try? await Net.get(url, accept: "application/geo+json"),
              let r = try? JSONDecoder().decode(Resp.self, from: data) else { return [] }
        let rank = ["Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3]
        return r.features.map { f in
            let p = f.properties
            return Alert(id: p.id, event: p.event, headline: p.headline ?? p.event, severity: p.severity ?? "Unknown",
                         ends: p.ends ?? p.expires, description: p.description ?? "")
        }.sorted { (rank[$0.severity] ?? 4) < (rank[$1.severity] ?? 4) }
    }

    private struct Resp: Decodable { var features: [Feature] = [] }
    private struct Feature: Decodable { var properties: Props }
    private struct Props: Decodable {
        var id: String
        var event: String
        var headline: String?
        var severity: String?
        var ends: String?
        var expires: String?
        var description: String?
    }
}

extension Array {
    subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil }
}
