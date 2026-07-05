import { BOULANGER_SKU } from '../constants/productIds';
import { fetchPlain } from './stealthFetch';

const SAFARI_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1';

export interface BoulangerGConfig {
  clientPromiseApiKey: string;
  clientGeographyApiKey: string;
  clientSiteApiKey: string;
  clientLocalStockEnabled?: boolean;
}

export interface BoulangerStoreCheck {
  inStock: boolean;
  availability: 'in_stock' | 'out_of_stock' | 'unknown';
  detail: string;
}

let cachedGConfig: BoulangerGConfig | null = null;

export function parseGConfig(html: string): BoulangerGConfig | null {
  const match = html.match(/var G_CONFIG = (\{[\s\S]*?\});/);
  if (!match) return null;
  try {
    const raw = JSON.parse(match[1]) as Record<string, unknown>;
    const keys = ['clientPromiseApiKey', 'clientGeographyApiKey', 'clientSiteApiKey'] as const;
    for (const k of keys) {
      if (typeof raw[k] !== 'string') return null;
    }
    return {
      clientPromiseApiKey: raw.clientPromiseApiKey as string,
      clientGeographyApiKey: raw.clientGeographyApiKey as string,
      clientSiteApiKey: raw.clientSiteApiKey as string,
      clientLocalStockEnabled: Boolean(raw.clientLocalStockEnabled),
    };
  } catch {
    return null;
  }
}

async function loadGConfig(): Promise<BoulangerGConfig | null> {
  if (cachedGConfig) return cachedGConfig;
  const html = await fetchPlain(`https://www.boulanger.com/ref/${BOULANGER_SKU}`);
  if (!html) return null;
  cachedGConfig = parseGConfig(html);
  return cachedGConfig;
}

async function resolveCityCode(postalCode: string, config: BoulangerGConfig): Promise<string | null> {
  try {
    const response = await fetch(
      'https://www.boulanger.com/api/referential/geography-v3/cities/search',
      {
        method: 'POST',
        headers: {
          'User-Agent': SAFARI_UA,
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Origin: 'https://www.boulanger.com',
          Referer: `https://www.boulanger.com/ref/${BOULANGER_SKU}`,
          'x-api-key': config.clientGeographyApiKey,
        },
        body: JSON.stringify({ filter: { zipCode: postalCode } }),
      },
    );
    if (!response.ok) return null;
    const json = (await response.json()) as {
      results?: Array<{ cityCode?: string }>;
    };
    return json.results?.[0]?.cityCode ?? null;
  } catch {
    return null;
  }
}

async function tryLocalStockApi(
  config: BoulangerGConfig,
  postalCode: string,
  cityCode: string | null,
  siteCode?: string,
): Promise<BoulangerStoreCheck | null> {
  const filter: Record<string, string> = {
    skuId: BOULANGER_SKU,
    zipCode: postalCode,
  };
  if (cityCode) filter.cityCode = cityCode;
  if (siteCode) filter.siteCode = siteCode;

  try {
    const response = await fetch(
      'https://www.boulanger.com/api/commerce/promise-v2/local-stock/search',
      {
        method: 'POST',
        headers: {
          'User-Agent': SAFARI_UA,
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Origin: 'https://www.boulanger.com',
          Referer: `https://www.boulanger.com/ref/${BOULANGER_SKU}`,
          'x-api-key': config.clientPromiseApiKey,
        },
        body: JSON.stringify({ filter }),
      },
    );
    if (response.status === 401 || response.status === 403) return null;
    if (!response.ok) return null;

    const json = (await response.json()) as {
      results?: Array<{ siteCode?: string; availability?: string; inStock?: boolean }>;
    };
    const rows = json.results ?? [];
    if (!rows.length) {
      return {
        inStock: false,
        availability: 'out_of_stock',
        detail: 'Boulanger: pas de stock local (API)',
      };
    }

    const row = siteCode
      ? rows.find((r) => r.siteCode === siteCode) ?? rows[0]
      : rows[0];

    const avail = (row.availability ?? '').toUpperCase();
    if (row.inStock || avail.includes('AVAILABLE') || avail.includes('STOCK')) {
      return {
        inStock: true,
        availability: 'in_stock',
        detail: 'Boulanger: stock magasin (API)',
      };
    }
    if (avail.includes('UNAVAILABLE') || avail.includes('OUT')) {
      return {
        inStock: false,
        availability: 'out_of_stock',
        detail: 'Boulanger: rupture magasin (API)',
      };
    }
    return null;
  } catch {
    return null;
  }
}

export async function checkBoulangerStore(
  postalCode: string,
  siteCode?: string,
): Promise<BoulangerStoreCheck> {
  const config = await loadGConfig();
  if (!config?.clientLocalStockEnabled) {
    return {
      inStock: false,
      availability: 'unknown',
      detail: 'Boulanger: stock magasin non exposé',
    };
  }

  const cityCode = await resolveCityCode(postalCode, config);
  const apiResult = await tryLocalStockApi(config, postalCode, cityCode, siteCode);
  if (apiResult) return apiResult;

  return {
    inStock: false,
    availability: 'unknown',
    detail: 'Boulanger: API magasin indisponible (auth)',
  };
}

export function boulangerProductUrl(): string {
  return `https://www.boulanger.com/ref/${BOULANGER_SKU}`;
}
