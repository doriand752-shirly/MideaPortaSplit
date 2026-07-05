import Foundation
import UserNotifications

@MainActor
final class NotificationService: ObservableObject {
    static let shared = NotificationService()

    @Published private(set) var authorizationGranted = false

    func requestAuthorization() async {
        let center = UNUserNotificationCenter.current()
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            authorizationGranted = granted
        } catch {
            authorizationGranted = false
        }
    }

    func notifyNewOffers(_ offers: [ActionableOffer]) async {
        guard authorizationGranted, !offers.isEmpty else { return }
        let center = UNUserNotificationCenter.current()

        for offer in offers {
            let content = UNMutableNotificationContent()
            content.title = offer.kind == .magasin
                ? "PortaSplit — retrait magasin"
                : "PortaSplit — livraison dispo"
            content.body = "\(offer.title)\n\(offer.detail)"
            content.sound = .default
            content.userInfo = ["url": offer.url]

            let request = UNNotificationRequest(
                identifier: "portasplit-\(offer.id)-\(UUID().uuidString)",
                content: content,
                trigger: nil
            )
            try? await center.add(request)
        }
    }

    func notifyHeartbeat(actionableCount: Int, postalCode: String) async {
        guard authorizationGranted else { return }
        let content = UNMutableNotificationContent()
        content.title = "PortaSplit — surveillance active"
        content.body = actionableCount > 0
            ? "\(actionableCount) offre(s) actionnable(s) autour de \(postalCode)"
            : "Aucun stock actionnable pour \(postalCode) pour l'instant"
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "portasplit-heartbeat-\(UUID().uuidString)",
            content: content,
            trigger: nil
        )
        try? await UNUserNotificationCenter.current().add(request)
    }
}
