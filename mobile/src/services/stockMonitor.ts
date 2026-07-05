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
  if (!cloud) return null;

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

async function performCheck(settings: AppSettings) {
  if (settings.cloudMonitorEnabled) {
    const cloud = await performCloudCheck(settings);
    if (cloud) return cloud;
  }
  return performLocalCheck(settings);
}

export async function runStockCheck(
  settings: AppSettings,
): Promise<{ snapshot: MonitorSnapshot; newOffers: ActionableOffer[] }> {
  const first = await performCheck(settings);
  let actionable = first.actionable;

  if (settings.confirmStock && first.dataMode !== 'cloud' && actionable.length > 0) {
    await sleep(3000);
    const second = await performCheck(settings);
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
