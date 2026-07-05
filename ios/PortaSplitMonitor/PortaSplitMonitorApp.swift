import SwiftUI

@main
struct PortaSplitMonitorApp: App {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var monitor = StockMonitor.shared

    init() {
        BackgroundRefreshService.register()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(monitor)
                .task {
                    await NotificationService.shared.requestAuthorization()
                }
                .onChange(of: scenePhase) { _, phase in
                    handleScenePhase(phase)
                }
        }
    }

    private func handleScenePhase(_ phase: ScenePhase) {
        let settings = SettingsStore.shared.load()
        switch phase {
        case .active:
            if settings.backgroundRefreshEnabled || monitor.monitoringActive {
                monitor.start(settings: settings)
            }
        case .background:
            if settings.backgroundRefreshEnabled {
                BackgroundRefreshService.scheduleNext(afterMinutes: settings.intervalMinutes)
            }
        default:
            break
        }
    }
}
