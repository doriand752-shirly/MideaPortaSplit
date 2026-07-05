import { allowedDepartments } from '../constants/departments';
import { NEARBY_STORES, PICKUP_RETAILER_IDS, STORE_CHECK_DELAY_MS } from '../constants/nearbyStores';
import { productUrlForRetailer } from '../constants/retailers';
import type { LocalStoreOffer } from '../types';
import { fetchCastoramaLocalStores } from './castoramaKingfisher';
import { distanceKm, geocodePostalCode } from './geocoding';
import { fetchLeroyMerlinLocalStores } from './leroyMerlinStockApi';
import { checkStoreProduct } from './storeProductChecker';

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jitter(baseMs: number): Promise<void> {
  return sleep(baseMs + Math.floor(Math.random() * 500));
}

function mergeById(stores: LocalStoreOffer[]): LocalStoreOffer[] {
  const map = new Map<string, LocalStoreOffer>();
  for (const s of stores) {
    const existing = map.get(s.id);
    if (!existing || (s.inStock && !existing.inStock)) map.set(s.id, s);
  }
  return [...map.values()];
}

/**
 * Magasins LM + Castorama via APIs du checker clim-portasplit-checker,
 * Boulanger/Darty via page produit (secondaire).
 */
export async function fetchIndependentLocalStores(
  postalCode: string,
  radiusKm: number,
): Promise<LocalStoreOffer[]> {
  const userPoint = await geocodePostalCode(postalCode);
  const allowedDepts = allowedDepartments(postalCode);

  const [castoStores, lmStores] = await Promise.all([
    fetchCastoramaLocalStores(userPoint, radiusKm, allowedDepts),
    fetchLeroyMerlinLocalStores(userPoint, radiusKm, allowedDepts),
  ]);

  const catalogStores: LocalStoreOffer[] = [];
  for (const store of NEARBY_STORES) {
    if (!allowedDepts.has(store.postalCode.slice(0, 2))) continue;
    if (store.retailerId === 'castorama' || store.retailerId === 'leroy_merlin') continue;

    let storePoint;
    try {
      storePoint = await geocodePostalCode(store.postalCode);
    } catch {
      continue;
    }
    const dist = distanceKm(
      { lat: userPoint.lat, lon: userPoint.lon, dept: '' },
      storePoint,
    );
    if (dist > radiusKm) continue;

    catalogStores.push({
      id: `local:${store.retailerId}:${store.postalCode}:${store.id}`,
      storeName: store.name,
      retailerId: store.retailerId,
      location: `${store.city.toUpperCase()} ${store.postalCode}`,
      postalCode: store.postalCode,
      department: store.postalCode.slice(0, 2),
      distanceKm: Math.round(dist * 10) / 10,
      inStock: false,
      price: null,
      productURL: productUrlForRetailer(store.retailerId),
      lastUpdateMin: null,
      stockSource: 'unknown',
    });
  }

  for (const offer of catalogStores) {
    if (!PICKUP_RETAILER_IDS.has(offer.retailerId)) continue;
    const def = NEARBY_STORES.find((n) => offer.id.endsWith(`:${n.id}`));
    if (!def) continue;

    const check = await checkStoreProduct(def);
    offer.inStock = check.inStock;
    offer.price = check.price;
    offer.productURL = check.productURL;
    offer.stockNote = check.detail;
    offer.stockSource = check.availability === 'unknown' ? 'unknown' : 'direct_store';
    await jitter(STORE_CHECK_DELAY_MS);
  }

  return mergeById([...castoStores, ...lmStores, ...catalogStores]).sort((a, b) => {
    if (a.inStock !== b.inStock) return a.inStock ? -1 : 1;
    return a.distanceKm - b.distanceKm;
  });
}
