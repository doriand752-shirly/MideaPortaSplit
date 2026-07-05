export type StockKind = 'magasin' | 'livraison';

export interface OnlineOffer {
  id: string;
  retailerName: string;
  inStock: boolean;
  price: number | null;
  url: string;
  deliveryEligible: boolean;
  lastUpdateMin: number | null;
  sources?: ('climradar' | 'direct')[];
  sourceDetail?: string;
  directDetail?: string;
  /** Vérification site en échec (anti-bot, réseau…) — afficher quand même. */
  checkError?: boolean;
}

export interface LocalStoreOffer {
  id: string;
  storeName: string;
  retailerId: string;
  location: string;
  postalCode: string;
  department: string;
  distanceKm: number;
  inStock: boolean;
  price: number | null;
  productURL: string;
  lastUpdateMin: number | null;
  stockSource?: 'climradar' | 'direct_store' | 'online_proxy' | 'unknown';
  stockNote?: string;
}

export type DataMode = 'hybrid' | 'independent' | 'climradar';

export interface ActionableOffer {
  id: string;
  kind: StockKind;
  title: string;
  detail: string;
  url: string;
  price: number | null;
}

export interface MonitorSnapshot {
  checkedAt: string;
  postalCode: string;
  radiusKm: number;
  monitoredDepartments: string[];
  onlineOffers: OnlineOffer[];
  localStores: LocalStoreOffer[];
  actionable: ActionableOffer[];
  dataMode?: DataMode;
  climradarAvailable?: boolean;
  errorMessage?: string;
}

export interface AppSettings {
  postalCode: string;
  radiusKm: number;
  intervalMinutes: number;
  confirmStock: boolean;
  monitoringEnabled: boolean;
  showOutOfStock: boolean;
  backgroundFetchEnabled: boolean;
  directCheckEnabled: boolean;
  climradarEnabled: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
  postalCode: '33400',
  radiusKm: 200,
  intervalMinutes: 2,
  confirmStock: true,
  monitoringEnabled: true,
  showOutOfStock: true,
  backgroundFetchEnabled: true,
  directCheckEnabled: true,
  climradarEnabled: true,
};

export function formatLastUpdate(min: number | null): string {
  if (min == null) return 'MAJ inconnue';
  if (min < 1) return 'MAJ à l\'instant';
  if (min < 60) return `MAJ il y a ${min} min`;
  const hours = Math.floor(min / 60);
  if (hours < 24) return `MAJ il y a ${hours} h`;
  return `MAJ il y a ${Math.floor(hours / 24)} j`;
}
