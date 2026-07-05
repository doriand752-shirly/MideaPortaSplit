/** Détection stock Amazon.fr — zone buybox uniquement (évite les faux positifs marketplace / associés). */

const AMAZON_OUT_OF_STOCK = [
  /actuellement indisponible/i,
  /currently unavailable/i,
  /nous ne savons pas quand/i,
  /we don't know when/i,
  /temporairement en rupture/i,
  /non disponible/i,
  /plus disponible/i,
  /indisponible/i,
];

export function extractAmazonBuybox(html: string): string {
  const patterns = [
    /id="buybox"[^>]*>([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>/i,
    /id="desktop_buybox"[^>]*>([\s\S]{0,35000})/i,
    /id="qualifiedBuybox"[^>]*>([\s\S]{0,35000})/i,
    /id="apex_desktop"[^>]*>([\s\S]{0,35000})/i,
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match?.[1] && match[1].length > 150) return match[1];
  }
  const cartIdx = html.search(/id="add-to-cart-button"/i);
  if (cartIdx >= 0) return html.slice(Math.max(0, cartIdx - 10_000), cartIdx + 10_000);
  return '';
}

export function extractAmazonAvailability(html: string): string {
  const match = html.match(/id="availability"[^>]*>([\s\S]*?)<\/div>/i);
  if (!match) return '';
  return match[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function hasBuyboxAddToCart(buybox: string): boolean {
  if (!buybox) return false;
  return (
    /id="add-to-cart-button"/i.test(buybox) ||
    /name="submit\.add-to-cart"/i.test(buybox) ||
    /id="submit\.add-to-cart"/i.test(buybox)
  );
}

function isCartDisabled(buybox: string): boolean {
  const cartIdx = buybox.search(/add-to-cart/i);
  if (cartIdx < 0) return false;
  const snippet = buybox.slice(Math.max(0, cartIdx - 200), cartIdx + 600).toLowerCase();
  return /disabled|a-button-disabled|aria-disabled="true"/.test(snippet);
}

export function detectAmazon(html: string): {
  inStock: boolean;
  detail: string;
  /** true = ne pas fusionner avec ClimRadar (buybox illisible) */
  uncertain?: boolean;
} {
  const buybox = extractAmazonBuybox(html);
  const availability = extractAmazonAvailability(html);
  const availLower = availability.toLowerCase();
  const buyboxLower = buybox.toLowerCase();
  const pageLower = html.toLowerCase();

  for (const pattern of AMAZON_OUT_OF_STOCK) {
    if (pattern.test(availLower)) {
      return { inStock: false, detail: `Amazon buybox: ${availability.slice(0, 80)}` };
    }
    if (buybox && pattern.test(buyboxLower)) {
      return { inStock: false, detail: 'Amazon buybox: indisponible' };
    }
  }

  const buyboxCart = hasBuyboxAddToCart(buybox);
  const thirdPartyOnly =
    !buyboxCart &&
    (/à partir de/i.test(pageLower) ||
      /autres vendeurs sur amazon/i.test(pageLower) ||
      /other sellers on amazon/i.test(pageLower) ||
      /all-offers-display/i.test(pageLower) ||
      /aod-container/i.test(pageLower));

  if (thirdPartyOnly) {
    return { inStock: false, detail: 'Amazon: revendeurs tiers uniquement (pas le buybox)' };
  }

  if (buyboxCart) {
    if (isCartDisabled(buybox)) {
      return { inStock: false, detail: 'Amazon: bouton panier désactivé' };
    }
    if (/en stock|in stock/i.test(availLower) || /en stock/i.test(buyboxLower)) {
      return { inStock: true, detail: 'Amazon buybox: en stock' };
    }
    return { inStock: true, detail: 'Amazon buybox: ajouter au panier actif' };
  }

  if (/"isBuyBoxWinner"\s*:\s*true/i.test(html) && /"maxQuantity"\s*:\s*[1-9]/i.test(html)) {
    return { inStock: true, detail: 'Amazon: buybox gagnant (JSON)' };
  }

  if (!buybox) {
    return { inStock: false, detail: 'Amazon: buybox introuvable', uncertain: true };
  }

  return { inStock: false, detail: 'Amazon buybox: pas de bouton panier' };
}

export function extractAmazonPrice(html: string, expected?: number): number | null {
  const buybox = extractAmazonBuybox(html);
  const scope = buybox || html;
  const values: number[] = [];

  const wholeMatch = scope.match(/class="a-price-whole"[^>]*>([\d\s]+)</i);
  if (wholeMatch) {
    const whole = Number(wholeMatch[1].replace(/\s/g, ''));
    const fracMatch = scope.match(/class="a-price-fraction"[^>]*>(\d+)/i);
    if (whole > 0) values.push(fracMatch ? whole + Number(fracMatch[1]) / 100 : whole);
  }

  for (const match of scope.matchAll(/"priceAmount"\s*:\s*(\d+(?:\.\d+)?)/g)) {
    values.push(Number(match[1]));
  }
  for (const match of scope.matchAll(/(\d{1,4}(?:[.,]\d{2})?)\s*€/g)) {
    const v = Number(match[1].replace(',', '.'));
    if (v >= 400 && v <= 2000) values.push(v);
  }

  if (!values.length) return null;
  if (expected) {
    const plausible = values.filter((v) => v >= expected * 0.5 && v <= expected * 2);
    if (!plausible.length) return null;
    return plausible.reduce((a, b) =>
      Math.abs(a - expected) <= Math.abs(b - expected) ? a : b,
    );
  }
  return Math.min(...values);
}
