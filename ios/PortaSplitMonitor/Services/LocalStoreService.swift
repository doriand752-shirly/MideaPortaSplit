import Foundation

enum LocalStoreService {
    private static let slugToRetailerId: [String: String] = [
        "leroy-merlin": "leroy_merlin",
        "castorama": "castorama",
        "boulanger": "boulanger",
        "darty": "darty",
        "fnac": "fnac",
        "manomano": "manomano",
    ]

    private static let cityPostalOverrides: [String: String] = [
        "mérignac": "33700",
        "merignac": "33700",
        "gradignan": "33170",
        "lormont": "33310",
        "villenave d'ornon": "33140",
        "bordeaux": "33000",
    ]

    private static let defaultProductURL =
        "https://www.leroymerlin.fr/produits/climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html"

    static func fetchLocalStores(
        postalCode: String,
        radiusKm: Double,
        html: String
    ) async throws -> [LocalStoreOffer] {
        let geocoder = GeocodingService.shared
        let userPoint = try await geocoder.geocode(postalCode: postalCode)
        let userDept = userPoint.department

        var stores: [LocalStoreOffer] = []
        var seen = Set<String>()

        for row in parseStoreEntries(html) {
            guard slugToRetailerId[row.retailerSlug] != nil else { continue }

            let resolvedPostal = resolvePostal(city: row.city, rawPostal: row.rawPostal, userDept: userDept)
            guard !resolvedPostal.isEmpty, resolvedPostal.prefix(2) == userDept.prefix(2) else { continue }

            let storePoint = try await geocoder.geocode(postalCode: resolvedPostal)
            let distance = await geocoder.distanceKm(from: userPoint, to: storePoint)
            guard distance <= radiusKm else { continue }

            let retailerId = slugToRetailerId[row.retailerSlug]!
            let dedupe = "\(retailerId):\(resolvedPostal):\(row.name)"
            guard !seen.contains(dedupe) else { continue }
            seen.insert(dedupe)

            let location = row.city.isEmpty ? resolvedPostal : "\(row.city.uppercased()) \(resolvedPostal)"
            let safeName = row.name.lowercased()
                .replacingOccurrences(of: "[^a-z0-9]+", with: "-", options: .regularExpression)
                .trimmingCharacters(in: CharacterSet(charactersIn: "-"))

            stores.append(
                LocalStoreOffer(
                    id: "local:\(retailerId):\(resolvedPostal):\(safeName)",
                    storeName: row.name,
                    retailerId: retailerId,
                    location: location,
                    postalCode: resolvedPostal,
                    distanceKm: (distance * 10).rounded() / 10,
                    inStock: row.inStock,
                    price: row.price,
                    productURL: row.storeURL.isEmpty ? defaultProductURL : row.storeURL
                )
            )
        }

        return stores.sorted {
            if $0.inStock != $1.inStock { return $0.inStock && !$1.inStock }
            return $0.distanceKm < $1.distanceKm
        }
    }

    private struct ParsedRow {
        let retailerSlug: String
        let name: String
        let city: String
        let rawPostal: String
        let storeURL: String
        let inStock: Bool
        let price: Double?
    }

    private static func parseStoreEntries(_ html: String) -> [ParsedRow] {
        guard let regex = try? NSRegularExpression(
            pattern: #"\\"store\\":\{(.*?)\\"entry\\":\{(.*?)\\"lastSeenMinAgo\\":\d+"#,
            options: [.dotMatchesLineSeparators]
        ) else { return [] }

        let range = NSRange(html.startIndex..<html.endIndex, in: html)
        let matches = regex.matches(in: html, range: range)
        var rows: [ParsedRow] = []

        for match in matches {
            guard
                match.numberOfRanges >= 3,
                let storeRange = Range(match.range(at: 1), in: html),
                let entryRange = Range(match.range(at: 2), in: html)
            else { continue }

            let storeText = unescape(String(html[storeRange]))
            let entryText = unescape(String(html[entryRange]))

            let retailer = field(storeText, key: "retailerId") ?? ""
            let name = decodeHTML(field(storeText, key: "name") ?? "")
            if name.isEmpty || name.lowercased() == "viewport" || name.lowercased() == "ville" {
                continue
            }

            let city = decodeHTML(field(storeText, key: "city") ?? "")
            let rawPostal = field(storeText, key: "postalCode") ?? ""
            let storeURL = field(storeText, key: "address") ?? ""
            let status = field(entryText, key: "status") ?? ""
            let price = field(entryText, key: "price").flatMap(Double.init)

            rows.append(
                ParsedRow(
                    retailerSlug: retailer,
                    name: name,
                    city: city,
                    rawPostal: rawPostal,
                    storeURL: storeURL,
                    inStock: status == "en_stock",
                    price: price
                )
            )
        }
        return rows
    }

    private static func resolvePostal(city: String, rawPostal: String, userDept: String) -> String {
        let cityKey = city.lowercased().trimmingCharacters(in: .whitespaces)
        if let override = cityPostalOverrides[cityKey] { return override }
        if rawPostal.count >= 2, rawPostal.prefix(2) == userDept.prefix(2) { return rawPostal }
        return rawPostal
    }

    private static func unescape(_ text: String) -> String {
        text.replacingOccurrences(of: "\\\"", with: "\"")
            .replacingOccurrences(of: "\\u0026", with: "&")
    }

    private static func field(_ text: String, key: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: #""\#(key)":"([^"]*)""#) else { return nil }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = regex.firstMatch(in: text, range: range), match.numberOfRanges > 1,
              let swiftRange = Range(match.range(at: 1), in: text) else { return nil }
        return String(text[swiftRange])
    }

    private static func decodeHTML(_ text: String) -> String {
        guard let data = text.data(using: .utf8) else { return text }
        let options: [NSAttributedString.DocumentReadingOptionKey: Any] = [
            .documentType: NSAttributedString.DocumentType.html,
            .characterEncoding: String.Encoding.utf8.rawValue,
        ]
        if let attributed = try? NSAttributedString(data: data, options: options, documentAttributes: nil) {
            return attributed.string
        }
        return text
    }
}
