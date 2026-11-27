import BackgroundTasks
import UserNotifications
import WidgetKit

// Background refresh for alerts and widgets. iOS decides when it runs (often
// every hour or two for an app that is used, less for one that is not), so
// these notifications are best effort. Severe weather alerts also show at the
// top of the app whenever it opens. Rain starting soon needs a check every
// 15 minutes, which iOS does not allow, so the iPhone app does not offer it.

enum Background {
    static let taskId = "com.peerloom.weatherglass.refresh"

    static func register() {
        UNUserNotificationCenter.current().delegate = NotificationShower.shared
        BGTaskScheduler.shared.register(forTaskWithIdentifier: taskId, using: nil) { task in
            guard let task = task as? BGAppRefreshTask else { return }
            schedule()
            let work = Task {
                await run()
                task.setTaskCompleted(success: true)
            }
            task.expirationHandler = { work.cancel() }
        }
    }

    /// Ask iOS to wake the app in about an hour.
    static func schedule() {
        let req = BGAppRefreshTaskRequest(identifier: taskId)
        req.earliestBeginDate = Date(timeIntervalSinceNow: 60 * 60)
        try? BGTaskScheduler.shared.submit(req)
    }

    static func run() async {
        let store = Store.shared
        guard let p = store.selectedPlace(), !(p.isCurrent && p.lat == 0 && p.lon == 0),
              let f = await store.refreshIfStale(p, maxAge: 20 * 60) else { return }
        WidgetCenter.shared.reloadAllTimelines()
        let s = store.settings
        if s.alerts { Notifier.newAlerts(f.alerts, notify: true) }
        if s.freezeAlert { Notifier.freeze(f, thresholdC: s.freezeAtC) }
    }
}

/// Shows Weatherglass's own notifications while the app is open too.
final class NotificationShower: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationShower()
    func userNotificationCenter(_ c: UNUserNotificationCenter, willPresent n: UNNotification) async -> UNNotificationPresentationOptions {
        [.banner, .sound, .list]
    }
}

enum Notifier {
    static func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
    }

    /// Notify about alerts not seen before. In the app (notify false) they are
    /// only marked seen, since the banner is already on screen.
    static func newAlerts(_ alerts: [Alert], notify: Bool) {
        let d = Store.shared.defaults
        let seen = Set(d.stringArray(forKey: "seenAlerts") ?? [])
        // Forget alerts that have ended, so the list does not grow forever.
        d.set(alerts.map(\.id), forKey: "seenAlerts")
        guard notify else { return }
        for a in alerts where !seen.contains(a.id) {
            post(id: a.id, title: a.event, body: a.headline, critical: ["Extreme", "Severe"].contains(a.severity))
        }
    }

    /// Freeze tonight: checked from 4 pm to 10 pm place time, once a day, for
    /// the lowest temperature until 10 am tomorrow (as on Android).
    static func freeze(_ f: Forecast, thresholdC: Double) {
        let now = placeNow(f.utcOffsetSeconds)
        let utc = { var c = Calendar(identifier: .gregorian); c.timeZone = TimeZone(identifier: "UTC")!; return c }()
        let hour = utc.component(.hour, from: now)
        guard (16...21).contains(hour) else { return }
        let today = dayString(now)
        let d = Store.shared.defaults
        guard d.string(forKey: "lastFreezeDate") != today else { return }
        let startOfHour = utc.date(bySettingHour: hour, minute: 0, second: 0, of: now)!
        let until = utc.date(byAdding: .day, value: 1, to: utc.date(bySettingHour: 10, minute: 0, second: 0, of: now)!)!
        let low = f.hours.compactMap { h in parseLocal(h.time).map { ($0, h) } }
            .filter { $0.0 >= startOfHour && $0.0 <= until }
            .min { $0.1.tempC < $1.1.tempC }
        guard let (_, h) = low, h.tempC <= thresholdC else { return }
        d.set(today, forKey: "lastFreezeDate")
        let s = Store.shared.settings
        post(id: "freeze-\(today)", title: "Freeze tonight",
             body: "Low of \(tempText(h.tempC, s.tempUnit)) around \(hourLabel(h.time, use24h: s.use24h)) in \(f.place.name).", critical: false)
    }

    private static func post(id: String, title: String, body: String, critical: Bool) {
        let c = UNMutableNotificationContent()
        c.title = title
        c.body = body
        c.sound = .default
        if critical { c.interruptionLevel = .timeSensitive }
        UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: id, content: c, trigger: nil))
    }
}
