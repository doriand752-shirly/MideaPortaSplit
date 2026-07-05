import {
  MONITORED_RETAILERS,
  PROTECTED_RETAILER_IDS,
  type DirectCheckResult,
  type RetailerConfig,
} from '../constants/retailers';
import { detectAmazon, extractAmazonPrice } from './amazonDetector';
import { fetchCastoramaOnline } from './castoramaKingfisher';
import { fetchForRetailer, isBotBlocked } from './stealthFetch';

const OUT_OF_STOCK = [
  /rupture\s+de\s+stock/i,
  /temporairement\s+indisponible/i,
  /non\s+disponible/i,
  /épuisé/i,
  /epuise/i,
  /outofstock/i,
  /schema\.org\/outofstock/i,
  /"availability"\s*:\s*"[^"]*outofstock/i,
  /actuellement indisponible/i,
  /currently unavailable/i,
  /indisponible en ligne/i,
];

const IN_STOCK = [
  /ajouter\s+au\s+panier/i,
  /schema\.org\/instock/i,
  /"availability"\s*:\s*"[^"]*instock/i,
  /add-to-cart/i,
  /addtocart/i,
  /in-stock/i,
  /"stock"\s*:\s*"available"/i,
  /"stockAvailability"\s*:\s*"available"/i,
];

const PRICE_RE = /(\d{1,4}(?:[.,]\d{2})?)\s*€/g;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function extractPrice(html: string, expected?: number): number | null {
  const values: number[] = [];
  let match: RegExpExecArray | null;
  while ((match = PRICE_RE.exec(html)) !== null) {
    const v = Number(match[1].replace(',', '.'));
    if (v >= 400 && v <= 2000) values.push(v);
  }
  if (!values.length) return null;
  if (expected) {
    const plausible = values.filter((v) => v >= expected * 0.5);
    if (!plausible.length) return null;
    return plausible.reduce((a, b) =>
      Math.abs(a - expected) <= Math.abs(b - expected) ? a : b,
    );
  }
  return Math.max(...values);
}

function detectGeneric(html: string): { inStock: boolean; detail: string } {
  const lower = html.toLowerCase();
  for (const p of OUT_OF_STOCK) {
    if (p.test(lower)) return { inStock: false, detail: 'Site: rupture détectée' };
  }
  if (/instock/i.test(html)) return { inStock: true, detail: 'Site: JSON-LD en stock' };
  for (const p of IN_STOCK) {
    if (p.test(lower)) return { inStock: true, detail: 'Site: disponible en ligne' };
  }
  return { inStock: false, detail: 'Site: statut inconnu' };
}

function detectWooCommerce(html: string): { inStock: boolean; detail: string } {
  const lower = html.toLowerCase();
  if (/out-of-stock|stock out-of-stock/.test(lower)) {
    return { inStock: false, detail: 'Optimea: rupture' };
  }
  if (/in-stock/.test(lower) && /single_add_to_cart_button/.test(lower)) {
    return { inStock: true, detail: 'Optimea: en stock' };
  }
  return detectGeneric(html);
}

function detect(
  retailer: RetailerConfig,
  html: string,
): { inStock: boolean; detail: string; uncertain?: boolean } {
  switch (retailer.checker) {
    case 'amazon':
      return detectAmazon(html);
    case 'woocommerce':
      return detectWooCommerce(html);
    default:
      return detectGeneric(html);
  }
}

function errorResult(retailer: RetailerConfig, detail: string): DirectCheckResult {
  return {
    id: retailer.id,
    retailerName: retailer.name,
    inStock: false,
    price: null,
    url: retailer.url,
    deliveryEligible: false,
    detail,
    source: 'direct',
    error: true,
  };
}

async function checkCastoramaDirect(
  retailer: RetailerConfig,
  postalCode: string,
): Promise<DirectCheckResult> {
  const online = await fetchCastoramaOnline(postalCode);
  if (online.available) {
    return {
      id: retailer.id,
      retailerName: retailer.name,
      inStock: true,
      price: retailer.expectedPrice ?? null,
      url: retailer.url,
      deliveryEligible: true,
      detail: online.message || `Castorama: ${online.homeDelivery ?? 'livraison OK'}`,
      source: 'direct',
    };
  }
  const html = await fetchForRetailer(retailer.url, retailer.id);
  if (!html) return errorResult(retailer, 'Castorama: API + page inaccessibles');
  const { inStock, detail } = detectGeneric(html);
  return {
    id: retailer.id,
    retailerName: retailer.name,
    inStock,
    price: extractPrice(html, retailer.expectedPrice),
    url: retailer.url,
    deliveryEligible: inStock,
    detail: online.message ? `Site: ${detail} · ${online.message}` : detail,
    source: 'direct',
  };
}

async function checkRetailer(
  retailer: RetailerConfig,
  postalCode: string,
): Promise<DirectCheckResult> {
  if (retailer.id === 'castorama') {
    return checkCastoramaDirect(retailer, postalCode);
  }

  const html = await fetchForRetailer(retailer.url, retailer.id);
  if (!html) {
    const blocked = PROTECTED_RETAILER_IDS.has(retailer.id);
    return errorResult(
      retailer,
      blocked
        ? 'Site: anti-bot actif (ClimRadar utilisé à la place)'
        : 'Site: inaccessible (erreur réseau)',
    );
  }

  if (isBotBlocked(html)) {
    return errorResult(retailer, 'Site: page captcha détectée');
  }

  const { inStock, detail, uncertain } = detect(retailer, html);
  if (uncertain) {
    return errorResult(retailer, `${detail} (ClimRadar utilisé)`);
  }

  const price =
    retailer.checker === 'amazon'
      ? extractAmazonPrice(html, retailer.expectedPrice)
      : extractPrice(html, retailer.expectedPrice);

  return {
    id: retailer.id,
    retailerName: retailer.name,
    inStock,
    price,
    url: retailer.url,
    deliveryEligible: retailer.deliveryEligible && inStock,
    detail,
    source: 'direct',
  };
}

export async function checkAllDirect(postalCode = '33400'): Promise<DirectCheckResult[]> {
  const open = MONITORED_RETAILERS.filter((r) => !PROTECTED_RETAILER_IDS.has(r.id));
  const protectedOnes = MONITORED_RETAILERS.filter((r) => PROTECTED_RETAILER_IDS.has(r.id));

  const openResults = await Promise.all(open.map((r) => checkRetailer(r, postalCode)));

  const protectedResults: DirectCheckResult[] = [];
  for (const retailer of protectedOnes) {
    protectedResults.push(await checkRetailer(retailer, postalCode));
    await sleep(1200 + Math.floor(Math.random() * 500));
  }

  return [...openResults, ...protectedResults];
}
