/** Revendeurs vérifiés en direct (site officiel) en plus de ClimRadar. */

/** URLs produit PortaSplit par revendeur (fallback si ClimRadar ne fournit pas de lien). */
export const RETAILER_PRODUCT_URLS: Record<string, string> = {
  amazon: 'https://www.amazon.fr/dp/B0D3PP64JS',
  darty:
    'https://www.darty.com/nav/achat/petit_electromenager/traitement_air/climatiseur/midea_mmcs-12hrn8-qrd0.html',
  boulanger: 'https://www.boulanger.com/ref/1216685',
  castorama:
    'https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd',
  leroy_merlin:
    'https://www.leroymerlin.fr/produits/climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html',
  optimea: 'https://www.optimea.fr/product/climatiseur-split-mobile-midea/',
  fnac:
    'https://www.fnac.com/SearchResult/ResultList.aspx?Search=portasplit+midea+MMCS-12HRN8&sa=Hist',
  manomano:
    'https://www.manomano.fr/p/midea-climatiseur-split-mobile-reversible-froid-chaud-3500w12000btu-wifi-deshumidificateur-ventilateur-jusqua-40m2-kit-fenetre-inclus-83810402',
};

export const RETAILER_SUBPAGES = ['leroy-merlin', 'castorama', 'boulanger', 'darty'] as const;

/** Sites avec protection anti-bot (DataDome, etc.) — requêtes séquentielles + warm-up. */
export const PROTECTED_RETAILER_IDS = new Set(['darty', 'leroy_merlin', 'fnac', 'manomano']);

export function productUrlForRetailer(retailerId: string, climradarUrl?: string): string {
  if (climradarUrl && climradarUrl.startsWith('http')) return climradarUrl;
  return RETAILER_PRODUCT_URLS[retailerId] ?? climradarUrl ?? '';
}

export interface RetailerConfig {
  id: string;
  name: string;
  url: string;
  checker: 'generic' | 'amazon' | 'woocommerce';
  deliveryEligible: boolean;
  expectedPrice?: number;
  /** Requête furtive (home → produit, délai) pour limiter la détection bot. */
  stealth?: boolean;
}

export const MONITORED_RETAILERS: RetailerConfig[] = [
  {
    id: 'boulanger',
    name: 'Boulanger',
    url: 'https://www.boulanger.com/ref/1216685',
    checker: 'generic',
    deliveryEligible: true,
    expectedPrice: 999,
  },
  {
    id: 'castorama',
    name: 'Castorama',
    url: 'https://www.castorama.fr/climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd',
    checker: 'generic',
    deliveryEligible: true,
    expectedPrice: 999,
  },
  {
    id: 'optimea',
    name: 'Optimea',
    url: 'https://www.optimea.fr/product/climatiseur-split-mobile-midea/',
    checker: 'woocommerce',
    deliveryEligible: true,
    expectedPrice: 999,
  },
  {
    id: 'amazon',
    name: 'Amazon',
    url: 'https://www.amazon.fr/dp/B0D3PP64JS',
    checker: 'amazon',
    deliveryEligible: true,
    expectedPrice: 999,
  },
  {
    id: 'manomano',
    name: 'ManoMano',
    url: 'https://www.manomano.fr/p/midea-climatiseur-split-mobile-reversible-froid-chaud-3500w12000btu-wifi-deshumidificateur-ventilateur-jusqua-40m2-kit-fenetre-inclus-83810402',
    checker: 'generic',
    deliveryEligible: true,
    expectedPrice: 999,
    stealth: true,
  },
  {
    id: 'darty',
    name: 'Darty',
    url: 'https://www.darty.com/nav/achat/petit_electromenager/traitement_air/climatiseur/midea_mmcs-12hrn8-qrd0.html',
    checker: 'generic',
    deliveryEligible: true,
    expectedPrice: 999,
    stealth: true,
  },
  {
    id: 'leroy_merlin',
    name: 'Leroy Merlin',
    url: RETAILER_PRODUCT_URLS.leroy_merlin,
    checker: 'generic',
    deliveryEligible: false,
    expectedPrice: 999,
    stealth: true,
  },
  {
    id: 'fnac',
    name: 'Fnac',
    url: RETAILER_PRODUCT_URLS.fnac,
    checker: 'generic',
    deliveryEligible: true,
    expectedPrice: 999,
    stealth: true,
  },
];

export type StockSource = 'climradar' | 'direct';

export interface DirectCheckResult {
  id: string;
  retailerName: string;
  inStock: boolean;
  price: number | null;
  url: string;
  deliveryEligible: boolean;
  detail: string;
  source: 'direct';
  error?: boolean;
}
