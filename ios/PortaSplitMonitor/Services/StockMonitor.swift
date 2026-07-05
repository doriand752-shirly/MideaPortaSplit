import Foundation

enum CheckSource: String {
    case foreground
    case background
    case manual
}

@MainActor
final class StockMonitor: ObservableObject {
    static let shared = StockMonitor()

    @Published private(set) var snapshot: MonitorSnapshot?
    @Published private(set) var isChecking = false
    @Published private(set) var lastError: String?
    @Published private(set) var monitoringActive = false

    private var timer: Timer?
    private var checkTask: Task<Void, Never>?
    private var inFlight = false

    func start(settings: AppSettings) {
        stopTimer()
        monitoringActive = true
        scheduleTimer(settings: settings)
        Task { await runCheck(settings: settings, source: .foreground) }
    }

    func stop() {
        monitoringActive = false
        stopTimer()
        checkTask?.cancel()
    }

    func runCheck(settings: AppSettings, source: CheckSource) async {
        guard !inFlight else { return }
        inFlight = true
        isChecking = true
        defer {
            inFlight = false
            isChecking = false
        }

        do {
            let first = try await performCheck(settings: settings)
            var actionable = first.actionable

            if settings.confirmStock, !actionable.isEmpty {
                try await Task.sleep(nanoseconds: 3_000_000_000)
                let second = try await performCheck(settings: settings)
                let secondIDs = Set(second.actionable.map(\.id))
                actionable = actionable.filter { secondIDs.contains($0.id) }
            }

            let newOffers = await AlertStateStore.shared.filterNewOffers(actionable)
            if !newOffers.isEmpty {
                await NotificationService.shared.notifyNewOffers(newOffers)
                await AlertStateStore.shared.markAlerted(newOffers)
            }

            await AlertStateStore.shared.clearUnavailable(activeIDs: Set(actionable.map(\.id)))

            snapshot = MonitorSnapshot(
                checkedAt: Date(),
                postalCode: settings.postalCode,
                radiusKm: settings.radiusKm,
                onlineOffers: first.onlineOffers,
                localStores: first.localStores,
                actionable: actionable,
                errorMessage: nil
            )
            lastError = nil

            if settings.backgroundRefreshEnabled {
                BackgroundRefreshService.scheduleNext(afterMinutes: settings.intervalMinutes)
            }
        } catch {
            lastError = error.localizedDescription
            snapshot = MonitorSnapshot(
                checkedAt: Date(),
                postalCode: settings.postalCode,
                radiusKm: settings.radiusKm,
                onlineOffers: snapshot?.onlineOffers ?? [],
                localStores: snapshot?.localStores ?? [],
                actionable: snapshot?.actionable ?? [],
                errorMessage: error.localizedDescription
            )
        }
    }

    func cancelInFlightCheck() {
        checkTask?.cancel()
    }

    private struct RawCheck {
        let onlineOffers: [OnlineOffer]
        let localStores: [LocalStoreOffer]
        let actionable: [ActionableOffer]
    }

    private func performCheck(settings: AppSettings) async throws -> RawCheck {
        let html = try await ClimRadarService.fetchProductHTML()
        let onlineOffers = ClimRadarService.parseOnlineOffers(from: html)
        let local = try await LocalStoreService.fetchLocalStores(
            postalCode: settings.postalCode,
            radiusKm: settings.radiusKm,
            html: html
        )
        let actionable = buildActionable(
            online: onlineOffers,
            local: local,
            postalCode: settings.postalCode
        )
        return RawCheck(onlineOffers: onlineOffers, localStores: local, actionable: actionable)
    }

    private func buildActionable(
        online: [OnlineOffer],
        local: [LocalStoreOffer],
        postalCode: String
    ) -> [ActionableOffer] {
        var offers: [ActionableOffer] = []

        for store in local where store.inStock {
            offers.append(
                ActionableOffer(
                    id: store.id,
                    kind: .magasin,
                    title: store.storeName,
                    detail: "Retrait magasin — \(store.distanceKm) km de \(postalCode)",
                    url: store.productURL,
                    price: store.price
                )
            )
        }

        for item in online where item.deliveryEligible {
            offers.append(
                ActionableOffer(
                    id: "livraison:\(item.id)",
                    kind: .livraison,
                    title: item.retailerName,
                    detail: "Livraison vers \(postalCode)",
                    url: item.url,
                    price: item.price
                )
            )
        }

        return offers
    }

    private func scheduleTimer(settings: AppSettings) {
        let interval = max(TimeInterval(settings.intervalMinutes * 60), 60)
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { @MainActor in
                await self.runCheck(settings: SettingsStore.shared.load(), source: .foreground)
            }
        }
    }

    private func stopTimer() {
        timer?.invalidate()
        timer = nil
    }
}
