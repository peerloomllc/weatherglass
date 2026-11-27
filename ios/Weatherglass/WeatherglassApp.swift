import SwiftUI

@main
struct WeatherglassApp: App {
    @StateObject private var model = AppModel()
    @Environment(\.scenePhase) private var phase

    init() { Background.register() }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .onChange(of: phase) { _, p in
                    if p == .background { model.opens += 1; Background.schedule() }
                    if p == .active { Task { await model.refresh() } }
                }
        }
    }
}
