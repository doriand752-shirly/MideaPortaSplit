import Foundation

actor AlertStateStore {
    static let shared = AlertStateStore()

    private var alertedKeys: Set<String> = []
    private let storageKey = "portasplit.alerted"

    init() {
        if let saved = UserDefaults.standard.array(forKey: storageKey) as? [String] {
            alertedKeys = Set(saved)
        }
    }

    func filterNewOffers(_ offers: [ActionableOffer]) -> [ActionableOffer] {
        offers.filter { !alertedKeys.contains($0.id) }
    }

    func markAlerted(_ offers: [ActionableOffer]) {
        for offer in offers {
            alertedKeys.insert(offer.id)
        }
        UserDefaults.standard.set(Array(alertedKeys), forKey: storageKey)
    }

    func clearUnavailable(activeIDs: Set<String>) {
        alertedKeys = alertedKeys.intersection(activeIDs)
        UserDefaults.standard.set(Array(alertedKeys), forKey: storageKey)
    }
}
