/**
 * Castorama stock via API Kingfisher (comme clim-portasplit-checker).
 * @see https://github.com/MathisKGN/clim-portasplit-checker
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

import { CASTO_FRANCE_SEEDS } from '../constants/castoSeeds';
import {
  CASTORAMA_EAN,
  CASTORAMA_FULFILMENT_API,
  CASTORAMA_PRODUCT_PATH,
} from '../constants/productIds';
import type { LocalStoreOffer } from '../types';
import { distanceKm } from './geocoding';
import { fetchPlain } from './stealthFetch';

const TOKEN_KEY = 'portasplit.casto.token';
const TOKEN_TS_KEY = 'portasplit.casto.token.ts';
const TOKEN_TTL_MS = 6 * 3600 * 1000;

const STORE_API = 'https://api.kingfisher.com/v1/mobile/stores/CAFR';
const PRODUCT_URL = `https://www.castorama.fr/${CASTORAMA_PRODUCT_PATH}`;

const UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

const STOCK_IN = new Set(['instock', 'limitedstock', 'lowstock', 'instockonline']);
const STOCK_OUT = new Set(['outofstock']);
const STOCK_NOT_CARRIED = new Set(['notstockedinstore', 'notranged', 'notsold']);
const CC_AVAILABLE = new Set(['allavailable', 'someavailable', 'available']);

export interface CastoOnlineAvailability {
  available: boolean;
  homeDelivery?: string;
  message?: string;
  quantity?: number;
}

interface ParsedCastoStore {
  id: string;
  name: string;
  postalCode: string;
  lat: number | null;
  lon: number | null;
  distanceKm: number | null;
  inStock: boolean;
  stockLevel: string;
  quantity: number | null;
  ccAvailability: string;
  detail: string;
}

export function extractCastoramaToken(html: string): string | null {
  const i = html.indexOf('stores/CAFR');
  const window = i >= 0 ? html.slice(i, i + 800) : html;
  let m = window.match(/[Aa]uthorization\\?"\s*:\s*\\?"([^"\\]{20,200})/);
  if (m) return m[1].trim();
  m = html.match(/[Aa]uthorization\\?"\s*:\s*\\?"([^"\\]{20,200})/);
  return m?.[1]?.trim() ?? null;
}

async function loadCachedToken(): Promise<string | null> {
  try {
    const [token, ts] = await Promise.all([
      AsyncStorage.getItem(TOKEN_KEY),
      AsyncStorage.getItem(TOKEN_TS_KEY),
    ]);
    if (!token || !ts) return null;
    if (Date.now() - Number(ts) > TOKEN_TTL_MS) return null;
    return token;
  } catch {
    return null;
  }
}

async function saveToken(token: string): Promise<void> {
  await AsyncStorage.multiSet([
    [TOKEN_KEY, token],
    [TOKEN_TS_KEY, String(Date.now())],
  ]);
}

async function fetchToken(force = false): Promise<string | null> {
  if (!force) {
    const cached = await loadCachedToken();
    if (cached) return cached;
  }
  const html = await fetchPlain(PRODUCT_URL);
  if (!html) return null;
  const token = extractCastoramaToken(html);
  if (token) await saveToken(token);
  return token;
}

function classifyStore(
  stockLevel: string,
  quantity: number | null,
  ccAvailability: string,
): { inStock: boolean; detail: string } {
  const lvl = (stockLevel || '').toLowerCase();
  const cc = (ccAvailability || '').toLowerCase();
  const ccOk = CC_AVAILABLE.has(cc);

  if (STOCK_IN.has(lvl) || (quantity != null && quantity > 0)) {
    return { inStock: true, detail: `Stock: ${stockLevel || 'dispo'}${quantity != null ? ` (${quantity})` : ''}` };
  }
  if (ccOk) {
    return { inStock: true, detail: `Click & Collect: ${ccAvailability}` };
  }
  if (STOCK_OUT.has(lvl) || quantity === 0) {
    return { inStock: false, detail: 'Rupture magasin' };
  }
  if (STOCK_NOT_CARRIED.has(lvl)) {
    return { inStock: false, detail: 'Non vendu en magasin' };
  }
  return { inStock: false, detail: `Statut: ${stockLevel || cc || 'inconnu'}` };
}

function parseKingfisherStore(raw: Record<string, unknown>): ParsedCastoStore | null {
  const attr = (raw.attributes ?? {}) as Record<string, unknown>;
  const store = (attr.store ?? {}) as Record<string, unknown>;
  const geo = (store.geoCoordinates ?? {}) as Record<string, unknown>;

  const sid = String(raw.id ?? store.externalId ?? '');
  if (!sid) return null;

  const stock = (attr.stock ?? {}) as Record<string, unknown>;
  const products = (stock.products ?? []) as Array<Record<string, unknown>>;
  const p0 = products[0] ?? {};
  const stockLevel = String(p0.stockLevel ?? '');
  const quantity = typeof p0.quantity === 'number' ? p0.quantity : null;

  const cc = (attr.clickAndCollect ?? {}) as Record<string, unknown>;
  const summary = (cc.summary ?? {}) as Record<string, unknown>;
  const ccAvailability = String(summary.availability ?? '');

  const coords = (geo.coordinates ?? {}) as Record<string, unknown>;
  const lat = typeof coords.latitude === 'number' ? coords.latitude : null;
  const lon = typeof coords.longitude === 'number' ? coords.longitude : null;

  const postalCode = String(geo.postalCode ?? '');
  const distRaw = String(store.distance ?? '');
  const distMatch = distRaw.match(/([\d.]+)/);
  const distanceKm = distMatch ? Number(distMatch[1]) : null;

  const { inStock, detail } = classifyStore(stockLevel, quantity, ccAvailability);

  return {
    id: sid,
    name: String(store.name ?? sid),
    postalCode,
    lat,
    lon,
    distanceKm,
    inStock,
    stockLevel,
    quantity,
    ccAvailability,
    detail,
  };
}

async function fetchStoresNear(
  token: string,
  lat: number,
  lon: number,
  pageSize = 50,
): Promise<ParsedCastoStore[]> {
  const params = new URLSearchParams({
    nearLatLong: `${lat},${lon}`,
    'page[size]': String(pageSize),
    include: 'clickAndCollect,stock',
    'filter[ean]': CASTORAMA_EAN,
  });

  try {
    const response = await fetch(`${STORE_API}?${params.toString()}`, {
      headers: {
        'User-Agent': UA,
        Authorization: token,
        Accept: 'application/json',
      },
    });
    if (response.status === 401) throw new Error('401');
    if (!response.ok) return [];
    const json = (await response.json()) as { data?: Record<string, unknown>[] };
    return (json.data ?? [])
      .map((row) => parseKingfisherStore(row))
      .filter((s): s is ParsedCastoStore => s != null);
  } catch (e) {
    if (e instanceof Error && e.message === '401') throw e;
    return [];
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchCastoramaOnline(postalCode: string): Promise<CastoOnlineAvailability> {
  const params = new URLSearchParams({
    compositeOfferId: CASTORAMA_EAN,
    delivery: 'true',
    postalCode,
  });
  try {
    const response = await fetch(`${CASTORAMA_FULFILMENT_API}?${params.toString()}`, {
      headers: {
        'User-Agent': UA,
        Accept: 'application/json',
        'Accept-Language': 'fr-FR,fr;q=0.9',
      },
    });
    if (!response.ok) return { available: false };
    const json = (await response.json()) as {
      data?: Array<{ attributes?: Record<string, unknown> }>;
    };
    const attrs = json.data?.[0]?.attributes ?? {};
    const hd = (attrs.homeDelivery ?? {}) as Record<string, unknown>;
    const avail = String(hd.availability ?? '').toLowerCase();
    return {
      available: ['available', 'instock', 'lowstock'].includes(avail),
      homeDelivery: String(hd.availability ?? ''),
      message: String(hd.shortMessage ?? hd.longMessage ?? ''),
      quantity: typeof hd.quantity === 'number' ? hd.quantity : undefined,
    };
  } catch {
    return { available: false };
  }
}

export async function fetchCastoramaLocalStores(
  userPoint: { lat: number; lon: number },
  radiusKm: number,
  allowedDepts: Set<string>,
): Promise<LocalStoreOffer[]> {
  let token = await fetchToken();
  if (!token) return [];

  const seeds: Array<{ lat: number; lon: number }> = [{ lat: userPoint.lat, lon: userPoint.lon }];
  if (radiusKm > 80) {
    for (const s of CASTO_FRANCE_SEEDS) seeds.push(s);
  }

  const byId = new Map<string, ParsedCastoStore>();

  for (let i = 0; i < seeds.length; i++) {
    const seed = seeds[i];
    try {
      const batch = await fetchStoresNear(token, seed.lat, seed.lon);
      for (const store of batch) {
        if (!byId.has(store.id)) byId.set(store.id, store);
      }
    } catch {
      token = await fetchToken(true);
      if (!token) break;
      try {
        const batch = await fetchStoresNear(token, seed.lat, seed.lon);
        for (const store of batch) {
          if (!byId.has(store.id)) byId.set(store.id, store);
        }
      } catch {
        break;
      }
    }
    if (i < seeds.length - 1) await sleep(900 + Math.floor(Math.random() * 400));
  }

  const offers: LocalStoreOffer[] = [];
  for (const store of byId.values()) {
    if (!store.postalCode || store.postalCode.length < 5) continue;
    const dept = store.postalCode.slice(0, 2);
    if (!allowedDepts.has(dept)) continue;

    const dist =
      store.distanceKm ??
      (store.lat != null && store.lon != null
        ? distanceKm(
            { lat: userPoint.lat, lon: userPoint.lon, dept: '' },
            { lat: store.lat, lon: store.lon, dept: '' },
          )
        : null);
    if (dist == null || dist > radiusKm) continue;

    offers.push({
      id: `local:castorama:${store.postalCode}:${store.id}`,
      storeName: store.name,
      retailerId: 'castorama',
      location: `${store.name.toUpperCase()} ${store.postalCode}`,
      postalCode: store.postalCode,
      department: dept,
      distanceKm: Math.round(dist * 10) / 10,
      inStock: store.inStock,
      price: null,
      productURL: `https://www.castorama.fr/store/${store.id}/${CASTORAMA_PRODUCT_PATH}`,
      lastUpdateMin: null,
      stockSource: 'direct_store',
      stockNote: store.detail,
    });
  }

  return offers;
}

export function castoramaProductUrl(): string {
  return PRODUCT_URL;
}
