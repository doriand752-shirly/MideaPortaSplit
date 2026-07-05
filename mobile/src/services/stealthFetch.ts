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

const BOT_PATTERNS = [
  /datadome/i,
  /captcha-delivery/i,
  /geo\.captcha/i,
  /challenge-platform/i,
  /please enable javascript/i,
  /access denied/i,
  /_Incapsula_Resource/i,
  /cf-browser-verification/i,
  /attention required/i,
  /bot detection/i,
  /interstitial/i,
  /hcaptcha/i,
  /recaptcha/i,
];

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
  return BOT_PATTERNS.some((p) => p.test(html));
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
