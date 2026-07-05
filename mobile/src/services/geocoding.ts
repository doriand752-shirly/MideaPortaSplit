const cache = new Map<string, { lat: number; lon: number; dept: string }>();

export interface GeoPoint {
  lat: number;
  lon: number;
  dept: string;
}

export async function geocodePostalCode(postalCode: string): Promise<GeoPoint> {
  const cached = cache.get(postalCode);
  if (cached) return cached;

  const url = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(postalCode)}&limit=1`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Géocodage impossible (${response.status})`);

  const json = await response.json();
  const feature = json.features?.[0];
  if (!feature) throw new Error(`Code postal introuvable : ${postalCode}`);

  const [lon, lat] = feature.geometry.coordinates;
  const dept = feature.properties?.depcode ?? postalCode.slice(0, 2);
  const point = { lat, lon, dept };
  cache.set(postalCode, point);
  return point;
}

export function distanceKm(a: GeoPoint, b: GeoPoint): number {
  const r = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(h));
}
