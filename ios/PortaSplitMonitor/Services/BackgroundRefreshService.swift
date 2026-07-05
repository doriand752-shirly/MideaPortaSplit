import BackgroundTasks
import Foundation

enum BackgroundRefreshService {
    static let taskIdentifier = "fr.portasplit.monitor.refresh"

    static func register() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: taskIdentifier, using: nil) { task in
            guard let refreshTask = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            handle(refreshTask)
        }
    }

    static func scheduleNext(afterMinutes minutes: Int) {
        let request = BGAppRefreshTaskRequest(identifier: taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: TimeInterval(max(minutes, 15) * 60))
        try? BGTaskScheduler.shared.submit(request)
    }

    private static func handle(_ task: BGAppRefreshTask) {
        let monitor = StockMonitor.shared
        let settings = SettingsStore.shared.load()

        task.expirationHandler = {
            Task { await monitor.cancelInFlightCheck() }
        }

        Task {
            await monitor.runCheck(settings: settings, source: .background)
            scheduleNext(afterMinutes: settings.intervalMinutes)
            task.setTaskCompleted(success: true)
        }
    }
}
