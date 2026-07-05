import Foundation

enum StockKind: String, Codable {
    case magasin
    case livraison
}

struct OnlineOffer: Identifiable, Codable, Hashable {
    let id: String
    let retailerName: String
    let inStock: Bool
    let price: Double?
    let url: String
    let deliveryEligible: Bool
}

struct LocalStoreOffer: Identifiable, Codable, Hashable {
    let id: String
    let storeName: String
    let retailerId: String
    let location: String
    let postalCode: String
    let distanceKm: Double
    let inStock: Bool
    let price: Double?
    let productURL: String
}

struct ActionableOffer: Identifiable, Codable, Hashable {
    let id: String
    let kind: StockKind
    let title: String
    let detail: String
    let url: String
    let price: Double?
}

struct MonitorSnapshot: Codable {
    let checkedAt: Date
    let postalCode: String
    let radiusKm: Double
    let onlineOffers: [OnlineOffer]
    let localStores: [LocalStoreOffer]
    let actionable: [ActionableOffer]
    let errorMessage: String?
}

struct AppSettings: Codable, Equatable {
    var postalCode: String
    var radiusKm: Double
    var intervalMinutes: Int
    var confirmStock: Bool
    var backgroundRefreshEnabled: Bool

    static let `default` = AppSettings(
        postalCode: "33400",
        radiusKm: 100,
        intervalMinutes: 2,
        confirmStock: true,
        backgroundRefreshEnabled: true
    )
}
