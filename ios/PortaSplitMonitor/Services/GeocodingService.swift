import CoreLocation
import Foundation

struct GeoPoint {
    let latitude: Double
    let longitude: Double
    let department: String
}

actor GeocodingService {
    static let shared = GeocodingService()

    private var cache: [String: GeoPoint] = [:]

    func geocode(postalCode: String) async throws -> GeoPoint {
        if let cached = cache[postalCode] {
            return cached
        }

        var components = URLComponents(string: "https://api-adresse.data.gouv.fr/search/")!
        components.queryItems = [
            URLQueryItem(name: "q", value: postalCode),
            URLQueryItem(name: "limit", value: "1"),
        ]

        let (data, response) = try await URLSession.shared.data(from: components.url!)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard
            let features = json?["features"] as? [[String: Any]],
            let first = features.first,
            let geometry = first["geometry"] as? [String: Any],
            let coords = geometry["coordinates"] as? [Double],
            coords.count >= 2,
            let props = first["properties"] as? [String: Any]
        else {
            throw URLError(.cannotFindHost)
        }

        let dept = (props["depcode"] as? String) ?? String(postalCode.prefix(2))
        let point = GeoPoint(latitude: coords[1], longitude: coords[0], department: dept)
        cache[postalCode] = point
        return point
    }

    func distanceKm(from: GeoPoint, to: GeoPoint) -> Double {
        Self.haversineKm(
            lat1: from.latitude, lon1: from.longitude,
            lat2: to.latitude, lon2: to.longitude
        )
    }

    nonisolated static func haversineKm(lat1: Double, lon1: Double, lat2: Double, lon2: Double) -> Double {
        let a = CLLocation(latitude: lat1, longitude: lon1)
        let b = CLLocation(latitude: lat2, longitude: lon2)
        return a.distance(from: b) / 1000.0
    }
}
