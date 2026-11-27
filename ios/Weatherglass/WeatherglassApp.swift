import SwiftUI

@main
struct WeatherglassApp: App {
    @StateObject private var model = AppModel()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .onChange(of: phase) { _, p in
                    if p == .background { model.opens += 1 }
                    if p == .active { Task { await model.refresh() } }
                }
        }
    }
}
