/**
 * Leroy Merlin stock via endpoint store-search-result (comme clim-portasplit-checker).
 * Sans navigateur Camoufox, DataDome peut bloquer → statut « inconnu ».
 * @see https://github.com/MathisKGN/clim-portasplit-checker
 */
import { LM_PRODUCT_ID } from '../constants/productIds';
import { NEARBY_STORES } from '../constants/nearbyStores';
import { productUrlForRetailer } from '../constants/retailers';
import type { LocalStoreOffer } from '../types';
import { distanceKm } from './geocoding';
import { fetchPlain, isBotBlocked } from './stealthFetch';

const PRODUCT_URL = productUrlForRetailer('leroy_merlin');
const STOCK_URL =
  'https://www.leroymerlin.fr/store-header-module/services/contextlayer/store-search-result';

const OUT_PATTERNS = ['indispo', 'rupture', 'epuis', 'non disponible'];
const UNKNOWN_PATTERNS = [
  'bientot',
  'prochainement',
  'temporairement',
  'sur commande',
  'reappro',
  'alerte',
  'prevenez-moi',
];
const IN_PATTERNS = ['disponible', 'en stock', 'plus que', 'retrait'];

function normalizeText(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function classifyLmStock(statusText: string, badgeClasses: string): { inStock: boolean; state: string } {
  const s = normalizeText(statusText);
  const b = (badgeClasses || '').toLowerCase();

  if (b.includes('--red') || OUT_PATTERNS.some((p) => s.includes(p))) {
    return { inStock: false, state: 'OUT' };
  }
  if (UNKNOWN_PATTERNS.some((p) => s.includes(p))) {
    return { inStock: false, state: 'UNKNOWN' };
  }
  if (b.includes('--green') || b.includes('--orange') || IN_PATTERNS.some((p) => s.includes(p))) {
    return { inStock: true, state: 'IN' };
  }
  return { inStock: false, state: 'UNKNOWN' };
}

export interface ParsedLmStore {
  slug: string;
  name: string;
  statusText: string;
  distanceKm: number | null;
  inStock: boolean;
  state: string;
}

export function parseLmStockHtml(html: string): ParsedLmStore[] {
  if (!html.includes('m-store-search-result') && html.toLowerCase().includes('<html')) {
    return [];
  }

  const slugs = new Set<string>();
  const slugRe = /\/magasins\/([a-z0-9-]+)\.html/gi;
  let m: RegExpExecArray | null;
  while ((m = slugRe.exec(html)) !== null) slugs.add(m[1].toLowerCase());

  const results: ParsedLmStore[] = [];
  for (const slug of slugs) {
    const idx = html.toLowerCase().indexOf(`/magasins/${slug}.html`);
    if (idx < 0) continue;
    const chunk = html.slice(Math.max(0, idx - 600), idx + 1800);

    const nameMatch =
      chunk.match(/store-info-header[^>]*>([^<]{2,80})</i) ??
      chunk.match(/main-store--title[^>]*>([^<]{2,80})</i) ??
      chunk.match(/store-name[^>]*>([^<]{2,80})</i);
    const badgeMatch = chunk.match(/stock-status[^"]*badge[^"]*"([^"]*)"/i);
    const textMatch = chunk.match(/stock-status__text[^>]*>([^<]+)/i);
    const distMatch = chunk.match(/([\d.,]+)\s*km/i);

    const statusText = textMatch?.[1]?.trim() ?? '';
    const badgeClasses = badgeMatch?.[1] ?? '';
    const { inStock, state } = classifyLmStock(statusText, badgeClasses);

    results.push({
      slug,
      name: nameMatch?.[1]?.trim() ?? slug,
      statusText,
      distanceKm: distMatch ? Number(distMatch[1].replace(',', '.')) : null,
      inStock,
      state,
    });
  }
  return results;
}

function isLmBlocked(status: number, body: string): boolean {
  if (status !== 200) return true;
  if (body.includes('m-store-search-result')) return false;
  const low = body.toLowerCase();
  if (low.includes('datadome') || low.includes('captcha')) return true;
  if (low.includes('<html')) return true;
  return false;
}

async function fetchLmStockFragment(lat: number, lon: number): Promise<{ status: number; body: string }> {
  await fetchPlain('https://www.leroymerlin.fr/');
  await sleep(800);
  await fetchPlain(PRODUCT_URL);
  await sleep(600);

  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lon),
    productRef: LM_PRODUCT_ID,
    storeSearchType: 'STOCK',
  });

  try {
    const response = await fetch(`${STOCK_URL}?${params.toString()}`, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        Accept: 'application/json, text/plain, */*',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        Referer: PRODUCT_URL,
        Origin: 'https://www.leroymerlin.fr',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
      },
    });
    const body = await response.text();
    return { status: response.status, body };
  } catch {
    return { status: -1, body: '' };
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildLmSeeds(lat: number, lon: number, radiusKm: number): Array<{ lat: number; lon: number }> {
  const seeds = [{ lat, lon }];
  if (radiusKm <= 40) return seeds;
  const step = 0.35;
  for (const [dlat, dlon] of [
    [step, 0],
    [-step, 0],
    [0, step * 1.2],
    [0, -step * 1.2],
  ]) {
    seeds.push({ lat: lat + dlat, lon: lon + dlon });
  }
  return seeds;
}

export async function fetchLeroyMerlinLocalStores(
  userPoint: { lat: number; lon: number },
  radiusKm: number,
  allowedDepts: Set<string>,
): Promise<LocalStoreOffer[]> {
  const seeds = buildLmSeeds(userPoint.lat, userPoint.lon, radiusKm);
  const bySlug = new Map<string, ParsedLmStore>();
  let blocked = 0;

  for (let i = 0; i < seeds.length; i++) {
    const { status, body } = await fetchLmStockFragment(seeds[i].lat, seeds[i].lon);
    if (isLmBlocked(status, body) || isBotBlocked(body)) {
      blocked += 1;
      if (blocked >= 2) break;
      continue;
    }
    for (const store of parseLmStockHtml(body)) {
      if (!bySlug.has(store.slug)) bySlug.set(store.slug, store);
    }
    if (i < seeds.length - 1) await sleep(2000 + Math.floor(Math.random() * 800));
  }

  if (!bySlug.size && blocked > 0) {
    return [];
  }

  const offers: LocalStoreOffer[] = [];
  for (const store of bySlug.values()) {
    const catalogMatch = NEARBY_STORES.find((s) => s.lmStoreSlug === store.slug);
    const postalCode = catalogMatch?.postalCode ?? '00000';
    const department = postalCode.slice(0, 2);

    const dist = store.distanceKm ?? 999;
    if (dist > radiusKm) continue;
    if (postalCode !== '00000' && !allowedDepts.has(department)) continue;

    offers.push({
      id: `local:leroy_merlin:${postalCode}:${store.slug}`,
      storeName: catalogMatch?.name ?? store.name,
      retailerId: 'leroy_merlin',
      location: catalogMatch
        ? `${catalogMatch.city.toUpperCase()} ${postalCode}`
        : store.name.toUpperCase(),
      postalCode,
      department: department === '00' ? (catalogMatch?.postalCode.slice(0, 2) ?? '00') : department,
      distanceKm: Math.round(dist * 10) / 10,
      inStock: store.inStock,
      price: null,
      productURL: `https://www.leroymerlin.fr/magasins/${store.slug}.html`,
      lastUpdateMin: null,
      stockSource: store.state === 'UNKNOWN' ? 'unknown' : 'direct_store',
      stockNote: store.statusText || store.state,
    });
  }

  return offers;
}
