/** Requêtes « navigateur » pour sites protégés (DataDome, etc.). */

const SAFARI_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1';

export const PROTECTED_RETAILER_IDS = new Set(['darty', 'leroy_merlin', 'fnac', 'manomano']);

const HOMEPAGES: Record<string, string> = {
  darty: 'https://www.darty.com/',
  leroy_merlin: 'https://www.leroymerlin.fr/',
  fnac: 'https://www.fnac.com/',
  manomano: 'https://www.manomano.fr/',
};

// Signaux fiables d'une vraie page de blocage (DataDome, Cloudflare, Incapsula...).
const STRONG_BOT_PATTERNS = [
  /datadome/i,
  /captcha-delivery/i,
  /geo\.captcha/i,
  /_Incapsula_Resource/i,
  /cf-browser-verification/i,
  /cf[_-]chl/i,
  /just a moment\.\.\./i,
  /attention required/i,
  /bot detection/i,
];

// Signaux ambigus : widgets/scripts presents aussi sur des pages produit legitimes.
const WEAK_BOT_PATTERNS = [
  /challenge-platform/i,
  /please enable javascript/i,
  /access denied/i,
  /interstitial/i,
  /hcaptcha/i,
  /recaptcha/i,
];

// Marqueurs d'une vraie page produit chargee (WooCommerce, JSON-LD, panier...).
const REAL_CONTENT_PATTERNS = [
  /add[_-]to[_-]cart/i,
  /single_add_to_cart_button/i,
  /woocommerce-Price-amount/i,
  /itemprop=["']price/i,
  /application\/ld\+json/i,
  /"availability"\s*:/i,
  /\b(in-stock|out-of-stock)\b/i,
  /rupture de stock/i,
];

function hasRealContent(html: string): boolean {
  return REAL_CONTENT_PATTERNS.filter((p) => p.test(html)).length >= 2;
}

function buildHeaders(referer?: string, sameOrigin = false): Record<string, string> {
  return {
    'User-Agent': SAFARI_UA,
    Accept:
      'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    Connection: 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': sameOrigin ? 'same-origin' : 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    ...(referer ? { Referer: referer } : {}),
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jitter(baseMs: number): Promise<void> {
  return sleep(baseMs + Math.floor(Math.random() * 700));
}

export function isBotBlocked(html: string): boolean {
  if (html.length < 800) return true;
  if (STRONG_BOT_PATTERNS.some((p) => p.test(html))) return true;
  // Les signaux faibles ne comptent que si la page n'a pas de vrai contenu produit.
  if (WEAK_BOT_PATTERNS.some((p) => p.test(html)) && !hasRealContent(html)) return true;
  return false;
}

async function fetchOnce(url: string, headers: Record<string, string>): Promise<Response | null> {
  try {
    return await fetch(url, { headers, redirect: 'follow' });
  } catch {
    return null;
  }
}

/** Page d’accueil puis produit, avec délai aléatoire (comportement utilisateur). */
export async function fetchStealth(url: string, retailerId: string): Promise<string | null> {
  const homepage = HOMEPAGES[retailerId];

  if (homepage) {
    const warm = await fetchOnce(homepage, buildHeaders());
    if (warm && !warm.ok && warm.status >= 403) return null;
    await jitter(850);
  }

  const referer = homepage ?? undefined;
  const response = await fetchOnce(url, buildHeaders(referer, Boolean(homepage)));
  if (!response?.ok) return null;

  const html = await response.text();
  if (isBotBlocked(html)) return null;
  return html;
}

export async function fetchPlain(url: string): Promise<string | null> {
  const response = await fetchOnce(url, buildHeaders());
  if (!response?.ok) return null;
  const html = await response.text();
  if (isBotBlocked(html)) return null;
  return html;
}

export async function fetchForRetailer(url: string, retailerId: string): Promise<string | null> {
  if (PROTECTED_RETAILER_IDS.has(retailerId)) {
    return fetchStealth(url, retailerId);
  }
  return fetchPlain(url);
}
