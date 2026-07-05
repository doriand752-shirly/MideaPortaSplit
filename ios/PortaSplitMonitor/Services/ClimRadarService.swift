import Foundation

enum ClimRadarService {
    private static let productURL = URL(string: "https://climradar.fr/produit/portasplit")!

    private static let retailerMap: [String: String] = [
        "Darty": "darty",
        "Boulanger": "boulanger",
        "Leroy Merlin": "leroy_merlin",
        "Castorama": "castorama",
        "Amazon": "amazon",
        "ManoMano": "manomano",
        "Fnac": "fnac",
    ]

    private static let deliveryRetailers: Set<String> = [
        "darty", "boulanger", "castorama", "optimea", "amazon", "fnac", "manomano",
    ]

    static func parseOnlineOffers(from html: String) -> [OnlineOffer] {
        parseJSONLOffers(html)
    }

    static func fetchOnlineOffers() async throws -> [OnlineOffer] {
        let html = try await fetchProductHTML()
        return parseJSONLOffers(html)
    }

    private static func parseJSONLOffers(_ html: String) -> [OnlineOffer] {
        var offers: [OnlineOffer] = []
        let chunks = html.components(separatedBy: "{\"@type\":\"Offer\"")
        for chunk in chunks.dropFirst() {
            guard
                let seller = firstMatch(in: chunk, pattern: #""name":"([^"]+)""#),
                let retailerId = retailerMap[seller]
            else { continue }

            let price = firstMatch(in: chunk, pattern: #""price":(\d+(?:\.\d+)?)"#).flatMap(Double.init)
            let availability = firstMatch(in: chunk, pattern: #""availability":"([^"]+)""#) ?? ""
            let url = firstMatch(in: chunk, pattern: #""url":"([^"]+)""#) ?? ""
            let area = firstMatch(in: chunk, pattern: #""areaServed":"([^"]*)""#) ?? ""
            if !area.isEmpty && area != "FR" { continue }

            let inStock = availability.contains("InStock")
            let deliveryEligible = deliveryRetailers.contains(retailerId) && retailerId != "leroy_merlin"

            offers.append(
                OnlineOffer(
                    id: retailerId,
                    retailerName: seller,
                    inStock: inStock,
                    price: price,
                    url: url,
                    deliveryEligible: deliveryEligible && inStock
                )
            )
        }
        return offers
    }

    static func fetchProductHTML() async throws -> String {
        var request = URLRequest(url: productURL)
        request.setValue(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
            forHTTPHeaderField: "User-Agent"
        )
        request.cachePolicy = .reloadIgnoringLocalCacheData
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return String(data: data, encoding: .utf8) ?? ""
    }

    private static func firstMatch(in text: String, pattern: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = regex.firstMatch(in: text, range: range), match.numberOfRanges > 1,
              let swiftRange = Range(match.range(at: 1), in: text) else { return nil }
        return String(text[swiftRange])
    }
}
