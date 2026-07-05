import { productUrlForRetailer } from '../constants/retailers';
import type { LocalStoreOffer, OnlineOffer } from '../types';

export const CLIMRADAR_PRODUCT_ID = 'portasplit';
export const CLIMRADAR_STOCK_URL = 'https://climradar.fr/api/stock';
export const CLIMRADAR_LIVE_URL = `https://climradar.fr/api/live?kind=product&id=${CLIMRADAR_PRODUCT_ID}`;

export const SLUG_TO_RETAILER_ID: Record<string, string> = {
  'leroy-merlin': 'leroy_merlin',
  castorama: 'castorama',
  boulanger: 'boulanger',
  darty: 'darty',
  fnac: 'fnac',
  manomano: 'manomano',
  amazon: 'amazon',
};

const DELIVERY_RETAILERS = new Set([
  'darty',
  'boulanger',
  'castorama',
  'optimea',
  'amazon',
  'fnac',
  'manomano',
]);

const FETCH_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
  Accept: 'application/json',
  'Accept-Language': 'fr-FR,fr;q=0.9',
};

export interface ClimradarRetailer {
  id: string;
  name: string;
}

export interface ClimradarStore {
  id: string;
  retailerId: string;
  channel: 'online' | 'store';
  name: string;
  country: string;
  address: string;
  city: string;
  postalCode: string;
  department: string;
  lat: number;
  lon: number;
}

export interface ClimradarEntry {
  storeId: string;
  productId: string;
  status: string;
  price: number | null;
  lastSeenMinAgo: number | null;
}

export interface ClimradarStockPayload {
  stores: ClimradarStore[];
  stockByStore: Record<string, ClimradarEntry[]>;
  retailers: ClimradarRetailer[];
  generatedAt?: string;
}

export interface ClimradarLiveRow {
  retailer: ClimradarRetailer;
  store: ClimradarStore;
  entry: ClimradarEntry;
  productUrl: string | null;
}

let stockCache: { fetchedAt: number; payload: ClimradarStockPayload } | null = null;
const STOCK_CACHE_MS = 60_000;

export async function fetchClimradarStock(force = false): Promise<ClimradarStockPayload | null> {
  const now = Date.now();
  if (!force && stockCache && now - stockCache.fetchedAt < STOCK_CACHE_MS) {
    return stockCache.payload;
  }

  try {
    const response = await fetch(CLIMRADAR_STOCK_URL, { headers: FETCH_HEADERS });
    if (!response.ok) return null;
    const payload = (await response.json()) as ClimradarStockPayload;
    if (!payload?.stores?.length || !payload.stockByStore) return null;
    stockCache = { fetchedAt: now, payload };
    return payload;
  } catch {
    return null;
  }
}

export async function fetchClimradarLiveRows(): Promise<ClimradarLiveRow[] | null> {
  try {
    const response = await fetch(CLIMRADAR_LIVE_URL, { headers: FETCH_HEADERS });
    if (!response.ok) return null;
    const json = (await response.json()) as { rows?: ClimradarLiveRow[] };
    return json.rows ?? null;
  } catch {
    return null;
  }
}

function entryForProduct(entries: ClimradarEntry[] | undefined): ClimradarEntry | null {
  if (!entries?.length) return null;
  return entries.find((e) => e.productId === CLIMRADAR_PRODUCT_ID) ?? entries[0];
}

function productUrlMapFromLive(rows: ClimradarLiveRow[] | null): Map<string, string> {
  const map = new Map<string, string>();
  if (!rows) return map;
  for (const row of rows) {
    if (row.productUrl?.startsWith('http')) {
      map.set(row.store.retailerId, row.productUrl);
      map.set(row.store.id, row.productUrl);
    }
  }
  return map;
}

export function isClimradarApiAvailable(payload: ClimradarStockPayload | null): boolean {
  return Boolean(payload?.stores?.length && payload.stockByStore);
}

export function parseOnlineOffersFromStock(
  payload: ClimradarStockPayload,
  liveRows?: ClimradarLiveRow[] | null,
): OnlineOffer[] {
  const storesById = new Map(payload.stores.map((s) => [s.id, s]));
  const retailersById = new Map(payload.retailers.map((r) => [r.id, r]));
  const productUrls = productUrlMapFromLive(liveRows ?? null);
  const offers: OnlineOffer[] = [];
  const seen = new Set<string>();

  for (const [storeId, entries] of Object.entries(payload.stockByStore)) {
    const store = storesById.get(storeId);
    if (!store || store.channel !== 'online' || store.country !== 'FR') continue;

    const entry = entryForProduct(entries);
    if (!entry) continue;

    const retailerId = SLUG_TO_RETAILER_ID[store.retailerId];
    if (!retailerId || seen.has(retailerId)) continue;
    seen.add(retailerId);

    const retailer = retailersById.get(store.retailerId);
    const inStock = entry.status === 'en_stock';
    const climradarUrl = productUrls.get(store.retailerId) ?? productUrls.get(storeId);
    const deliveryEligible =
      DELIVERY_RETAILERS.has(retailerId) && retailerId !== 'leroy_merlin' && inStock;

    offers.push({
      id: retailerId,
      retailerName: retailer?.name ?? store.name.replace(/ en ligne$/i, ''),
      inStock,
      price: entry.price ?? null,
      url: productUrlForRetailer(retailerId, climradarUrl),
      deliveryEligible,
      lastUpdateMin: entry.lastSeenMinAgo ?? null,
    });
  }

  return offers.sort((a, b) => a.retailerName.localeCompare(b.retailerName));
}

export function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const r = 6371;
  const p1 = (lat1 * Math.PI) / 180;
  const p2 = (lat2 * Math.PI) / 180;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(p1) * Math.cos(p2) * Math.sin(dLon / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(a));
}

export function parseLocalStoresFromStock(
  payload: ClimradarStockPayload,
  userLat: number,
  userLon: number,
  radiusKm: number,
  allowedDepts: Set<string>,
  liveRows?: ClimradarLiveRow[] | null,
): LocalStoreOffer[] {
  const storesById = new Map(payload.stores.map((s) => [s.id, s]));
  const productUrls = productUrlMapFromLive(liveRows ?? null);
  const stores: LocalStoreOffer[] = [];
  const seen = new Set<string>();

  for (const [storeId, entries] of Object.entries(payload.stockByStore)) {
    const store = storesById.get(storeId);
    if (!store || store.channel !== 'store' || store.country !== 'FR') continue;

    const retailerId = SLUG_TO_RETAILER_ID[store.retailerId];
    if (!retailerId) continue;

    const entry = entryForProduct(entries);
    if (!entry) continue;

    const dept = store.department || store.postalCode.slice(0, 2);
    if (dept && !allowedDepts.has(dept)) continue;

    const dist = haversineKm(userLat, userLon, store.lat, store.lon);
    if (dist > radiusKm) continue;

    const dedupe = `${retailerId}:${store.postalCode}:${store.name}`;
    if (seen.has(dedupe)) continue;
    seen.add(dedupe);

    const location = store.city
      ? `${store.city.toUpperCase()} ${store.postalCode}`
      : store.postalCode;
    const storePage = store.address.startsWith('http') ? store.address : '';
    const productUrl =
      productUrls.get(storeId) ??
      productUrls.get(store.retailerId) ??
      productUrlForRetailer(retailerId, storePage);
    const safeName = store.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

    stores.push({
      id: `local:${retailerId}:${store.postalCode}:${safeName}`,
      storeName: store.name,
      retailerId,
      location,
      postalCode: store.postalCode,
      department: dept,
      distanceKm: Math.round(dist * 10) / 10,
      inStock: entry.status === 'en_stock',
      price: entry.price ?? null,
      productURL: productUrl,
      lastUpdateMin: entry.lastSeenMinAgo ?? null,
      stockSource: 'climradar',
    });
  }

  return stores.sort((a, b) => {
    if (a.inStock !== b.inStock) return a.inStock ? -1 : 1;
    return a.distanceKm - b.distanceKm;
  });
}

export async function fetchClimradarOnlineOffers(): Promise<{
  offers: OnlineOffer[];
  available: boolean;
}> {
  const [payload, liveRows] = await Promise.all([
    fetchClimradarStock(),
    fetchClimradarLiveRows(),
  ]);
  if (!isClimradarApiAvailable(payload)) {
    return { offers: [], available: false };
  }
  const offers = parseOnlineOffersFromStock(payload!, liveRows);
  return { offers, available: offers.length > 0 };
}
