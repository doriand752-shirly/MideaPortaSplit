import { allowedDepartments, departmentLabel } from '../constants/departments';
import { adaptCloudSnapshot, fetchCloudSnapshot } from './cloudSnapshot';
import { fetchClimradarOnlineOffers } from './climradar';
import { checkAllDirect } from './directChecker';
import { fetchLocalStores, filterStores } from './localStores';
import { mergeOnlineOffers } from './mergeOffers';
import { loadAlertedKeys, saveAlertedKeys } from './settings';
import type {
  ActionableOffer,
  AppSettings,
  DataMode,
  LocalStoreOffer,
  MonitorSnapshot,
  OnlineOffer,
} from '../types';

export interface StockCheckOptions {
  /** Une seule verification locale (bouton manuel), ignore le mode snapshot. */
  forceLocal?: boolean;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildActionable(
  online: OnlineOffer[],
  local: LocalStoreOffer[],
  postalCode: string,
): ActionableOffer[] {
  const offers: ActionableOffer[] = [];

  for (const store of local) {
    if (!store.inStock) continue;
    const note =
      store.stockSource === 'unknown' && store.stockNote
        ? ` — ${store.stockNote}`
        : '';
    offers.push({
      id: store.id,
      kind: 'magasin',
      title: store.storeName,
      detail: `Retrait magasin — ${store.distanceKm} km de ${postalCode}${note}`,
      url: store.productURL,
      price: store.price,
    });
  }

  for (const item of online) {
    if (!item.deliveryEligible) continue;
    const sourceNote = item.sourceDetail ? ` · ${item.sourceDetail}` : '';
    offers.push({
      id: `livraison:${item.id}`,
      kind: 'livraison',
      title: item.retailerName,
      detail: `Livraison vers ${postalCode}${sourceNote}`,
      url: item.url,
      price: item.price,
    });
  }

  return offers;
}

async function resolveOnlineOffers(settings: AppSettings): Promise<{
  offers: OnlineOffer[];
  climradarAvailable: boolean;
}> {
  let climradarOffers: OnlineOffer[] = [];
  let climradarAvailable = false;

  if (settings.climradarEnabled) {
    const cr = await fetchClimradarOnlineOffers();
    climradarOffers = cr.offers;
    climradarAvailable = cr.available;
  }

  const directResults = settings.directCheckEnabled
    ? await checkAllDirect(settings.postalCode)
    : [];
  const offers = mergeOnlineOffers(climradarOffers, directResults, {
    directCheckEnabled: settings.directCheckEnabled,
  });

  return { offers, climradarAvailable };
}

async function performLocalCheck(settings: AppSettings) {
  const [{ offers: onlineOffers, climradarAvailable }, localResult] = await Promise.all([
    resolveOnlineOffers(settings),
    fetchLocalStores(settings.postalCode, settings.radiusKm, {
      climradarEnabled: settings.climradarEnabled,
    }),
  ]);

  const allLocal = localResult.stores;
  const localStores = filterStores(allLocal, settings.showOutOfStock);
  const actionable = buildActionable(onlineOffers, allLocal, settings.postalCode);
  const monitoredDepartments = [...allowedDepartments(settings.postalCode)].map(departmentLabel);

  let dataMode: DataMode = 'independent';
  if (settings.climradarEnabled && climradarAvailable && localResult.source === 'climradar') {
    dataMode = 'climradar';
  } else if (settings.climradarEnabled && (climradarAvailable || localResult.source === 'climradar')) {
    dataMode = 'hybrid';
  }

  return {
    onlineOffers,
    localStores,
    allLocal,
    actionable,
    monitoredDepartments,
    dataMode,
    climradarAvailable,
    checkedAt: new Date().toISOString(),
    errorMessage: undefined as string | undefined,
  };
}

async function performCloudCheck(settings: AppSettings) {
  const cloud = await fetchCloudSnapshot();
  if (!cloud) {
    throw new Error(
      'Snapshot cloud indisponible ou expiré. GitHub Actions met à jour toutes les 10 min.',
    );
  }

  const adapted = adaptCloudSnapshot(cloud, settings);
  return {
    onlineOffers: adapted.onlineOffers,
    localStores: adapted.localStores,
    allLocal: cloud.localStores,
    actionable: adapted.actionable,
    monitoredDepartments: adapted.monitoredDepartments,
    dataMode: 'cloud' as DataMode,
    climradarAvailable: adapted.climradarAvailable ?? true,
    checkedAt: adapted.checkedAt,
    errorMessage: adapted.errorMessage,
  };
}

async function performCheck(settings: AppSettings, options?: StockCheckOptions) {
  const useLocal = options?.forceLocal === true || settings.forceLocalCheck;
  if (useLocal) {
    return performLocalCheck(settings);
  }
  return performCloudCheck(settings);
}

export async function runStockCheck(
  settings: AppSettings,
  options?: StockCheckOptions,
): Promise<{ snapshot: MonitorSnapshot; newOffers: ActionableOffer[] }> {
  const useLocal = options?.forceLocal === true || settings.forceLocalCheck;
  const first = await performCheck(settings, options);
  let actionable = first.actionable;

  if (useLocal && settings.confirmStock && actionable.length > 0) {
    await sleep(3000);
    const second = await performCheck(settings, options);
    const secondIds = new Set(second.actionable.map((o) => o.id));
    actionable = actionable.filter((o) => secondIds.has(o.id));
  }

  const alerted = await loadAlertedKeys();
  const newOffers = actionable.filter((o) => !alerted.has(o.id));

  const activeIds = new Set(actionable.map((o) => o.id));
  const pruned = new Set([...alerted].filter((k) => activeIds.has(k)));
  for (const offer of newOffers) pruned.add(offer.id);
  await saveAlertedKeys(pruned);

  const snapshot: MonitorSnapshot = {
    checkedAt: first.checkedAt,
    postalCode: settings.postalCode,
    radiusKm: settings.radiusKm,
    monitoredDepartments: first.monitoredDepartments,
    onlineOffers: first.onlineOffers,
    localStores: first.localStores,
    actionable,
    dataMode: first.dataMode,
    climradarAvailable: first.climradarAvailable,
    errorMessage: first.errorMessage,
  };

  return { snapshot, newOffers };
}
