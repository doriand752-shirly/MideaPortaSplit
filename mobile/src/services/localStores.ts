import { allowedDepartments } from '../constants/departments';
import { fetchIndependentLocalStores } from './independentLocalStores';
import { geocodePostalCode } from './geocoding';
import {
  fetchClimradarLiveRows,
  fetchClimradarStock,
  isClimradarApiAvailable,
  parseLocalStoresFromStock,
} from './climradar';
import type { LocalStoreOffer } from '../types';

export async function fetchLocalStoresFromClimradar(
  postalCode: string,
  radiusKm: number,
): Promise<LocalStoreOffer[]> {
  const [payload, liveRows, userPoint] = await Promise.all([
    fetchClimradarStock(),
    fetchClimradarLiveRows(),
    geocodePostalCode(postalCode),
  ]);

  if (!isClimradarApiAvailable(payload)) return [];

  return parseLocalStoresFromStock(
    payload!,
    userPoint.lat,
    userPoint.lon,
    radiusKm,
    allowedDepartments(postalCode),
    liveRows,
  );
}

export async function fetchLocalStores(
  postalCode: string,
  radiusKm: number,
  options?: { climradarEnabled?: boolean },
): Promise<{ stores: LocalStoreOffer[]; source: 'climradar' | 'independent' }> {
  const useClimradar = options?.climradarEnabled !== false;
  if (useClimradar) {
    const climradarStores = await fetchLocalStoresFromClimradar(postalCode, radiusKm);
    if (climradarStores.length > 0) {
      return { stores: climradarStores, source: 'climradar' };
    }
  }
  const independent = await fetchIndependentLocalStores(postalCode, radiusKm);
  return { stores: independent, source: 'independent' };
}

export function filterStores(
  stores: LocalStoreOffer[],
  showOutOfStock: boolean,
): LocalStoreOffer[] {
  if (showOutOfStock) return stores;
  return stores.filter((s) => s.inStock);
}
