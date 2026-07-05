import type { NearbyStoreDef } from '../constants/nearbyStores';
import { productUrlForRetailer } from '../constants/retailers';
import { checkBoulangerStore, boulangerProductUrl } from './boulangerStoreApi';
import { fetchForRetailer, isBotBlocked } from './stealthFetch';

export interface StoreCheckResult {
  inStock: boolean;
  price: number | null;
  detail: string;
  availability: 'in_stock' | 'out_of_stock' | 'unknown';
  productURL: string;
}

const OUT_OF_STOCK = [
  /rupture\s+de\s+stock/i,
  /temporairement\s+indisponible/i,
  /non\s+disponible/i,
  /épuisé/i,
  /outofstock/i,
  /indisponible en magasin/i,
];

const IN_STOCK = [
  /disponible en magasin/i,
  /en stock en magasin/i,
  /retrait\s+(?:1\s*h|2\s*h|immédiat|magasin)/i,
  /click\s*&\s*collect/i,
  /schema\.org\/instock/i,
  /ajouter\s+au\s+panier/i,
];

const PRICE_RE = /(\d{1,4}(?:[.,]\d{2})?)\s*€/g;

function extractPrice(html: string): number | null {
  const values: number[] = [];
  let match: RegExpExecArray | null;
  while ((match = PRICE_RE.exec(html)) !== null) {
    const v = Number(match[1].replace(',', '.'));
    if (v >= 400 && v <= 2000) values.push(v);
  }
  return values.length ? Math.max(...values) : null;
}

function parseHtmlStoreStock(html: string, store: NearbyStoreDef): StoreCheckResult {
  const productURL = productUrlForRetailer(store.retailerId);
  if (isBotBlocked(html)) {
    return {
      inStock: false,
      price: null,
      availability: 'unknown',
      detail: 'Site: anti-bot (statut inconnu)',
      productURL,
    };
  }

  const cityPattern = store.city
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
  const lower = html.toLowerCase();
  const cityIdx = lower.indexOf(cityPattern);
  const scope =
    cityIdx >= 0
      ? html.slice(Math.max(0, cityIdx - 400), Math.min(html.length, cityIdx + 600))
      : html;

  for (const p of OUT_OF_STOCK) {
    if (p.test(scope)) {
      return {
        inStock: false,
        price: extractPrice(html),
        availability: 'out_of_stock',
        detail: `${store.name}: rupture détectée`,
        productURL,
      };
    }
  }
  for (const p of IN_STOCK) {
    if (p.test(scope)) {
      return {
        inStock: true,
        price: extractPrice(html),
        availability: 'in_stock',
        detail: `${store.name}: disponible (page produit)`,
        productURL,
      };
    }
  }

  return {
    inStock: false,
    price: extractPrice(html),
    availability: 'unknown',
    detail: `${store.name}: statut magasin inconnu`,
    productURL,
  };
}

async function checkDartyStore(store: NearbyStoreDef): Promise<StoreCheckResult> {
  const url = productUrlForRetailer('darty');
  const html = await fetchForRetailer(url, 'darty');
  if (!html) {
    return {
      inStock: false,
      price: null,
      availability: 'unknown',
      detail: 'Darty: page inaccessible (anti-bot)',
      productURL: url,
    };
  }
  return parseHtmlStoreStock(html, store);
}

/** Boulanger / Darty uniquement — LM et Castorama via APIs dédiées. */
export async function checkStoreProduct(store: NearbyStoreDef): Promise<StoreCheckResult> {
  switch (store.retailerId) {
    case 'boulanger': {
      const r = await checkBoulangerStore(store.postalCode, store.boulangerSiteCode);
      return {
        inStock: r.inStock,
        price: null,
        availability: r.availability,
        detail: r.detail,
        productURL: boulangerProductUrl(),
      };
    }
    case 'darty':
      return checkDartyStore(store);
    default:
      return {
        inStock: false,
        price: null,
        availability: 'unknown',
        detail: 'Enseigne non supportée',
        productURL: productUrlForRetailer(store.retailerId),
      };
  }
}
