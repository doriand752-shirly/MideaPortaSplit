import { MONITORED_RETAILERS, type StockSource } from '../constants/retailers';
import type { DirectCheckResult } from '../constants/retailers';
import type { OnlineOffer } from '../types';

function placeholderOffer(
  retailer: (typeof MONITORED_RETAILERS)[number],
  detail: string,
): OnlineOffer {
  return {
    id: retailer.id,
    retailerName: retailer.name,
    inStock: false,
    price: null,
    url: retailer.url,
    deliveryEligible: false,
    lastUpdateMin: null,
    sourceDetail: detail,
    checkError: true,
  };
}

function ensureAllDeliveryRetailers(
  map: Map<string, OnlineOffer>,
  directCheckEnabled: boolean,
): void {
  for (const retailer of MONITORED_RETAILERS) {
    if (!retailer.deliveryEligible) continue;
    if (map.has(retailer.id)) continue;
    map.set(
      retailer.id,
      placeholderOffer(
        retailer,
        directCheckEnabled
          ? 'Non vérifié cette fois'
          : 'Vérification directe désactivée (Réglages)',
      ),
    );
  }
}

export function mergeOnlineOffers(
  climradar: OnlineOffer[],
  direct: DirectCheckResult[],
  options?: { directCheckEnabled?: boolean },
): OnlineOffer[] {
  const map = new Map<string, OnlineOffer>();
  const directCheckEnabled = options?.directCheckEnabled !== false;

  for (const offer of climradar) {
    map.set(offer.id, {
      ...offer,
      sources: ['climradar'],
      sourceDetail: offer.sourceDetail ?? 'ClimRadar',
    });
  }

  for (const d of direct) {
    if (d.error) {
      const existing = map.get(d.id);
      if (existing) {
        const sources: StockSource[] = [...(existing.sources ?? ['climradar']), 'direct'];
        map.set(d.id, {
          ...existing,
          inStock: false,
          deliveryEligible: false,
          url: existing.url || d.url,
          sources,
          sourceDetail: d.detail,
          directDetail: d.detail,
          checkError: true,
        });
      } else {
        map.set(d.id, {
          id: d.id,
          retailerName: d.retailerName,
          inStock: false,
          price: null,
          url: d.url,
          deliveryEligible: false,
          lastUpdateMin: null,
          sources: ['direct'],
          sourceDetail: d.detail,
          directDetail: d.detail,
          checkError: true,
        });
      }
      continue;
    }

    const existing = map.get(d.id);
    const directEligible = d.deliveryEligible;

    if (existing) {
      const sources: StockSource[] = [...(existing.sources ?? ['climradar']), 'direct'];
      const inStock = existing.inStock || d.inStock;
      const deliveryEligible =
        (existing.deliveryEligible || directEligible) && inStock && d.id !== 'leroy_merlin';

      const parts: string[] = [];
      if (existing.sources?.includes('climradar') || !existing.sources) {
        parts.push(`ClimRadar: ${existing.inStock ? 'OK' : 'non'}`);
      }
      parts.push(`Site: ${d.inStock ? 'OK' : 'non'}`);
      if (existing.inStock !== d.inStock) {
        parts.push('sources divergentes');
      }

      map.set(d.id, {
        ...existing,
        inStock,
        deliveryEligible,
        price: d.price ?? existing.price,
        url: existing.url || d.url,
        sources,
        sourceDetail: parts.join(' · '),
        directDetail: d.detail,
        checkError: false,
      });
    } else {
      map.set(d.id, {
        id: d.id,
        retailerName: d.retailerName,
        inStock: d.inStock,
        price: d.price,
        url: d.url,
        deliveryEligible: directEligible,
        lastUpdateMin: null,
        sources: ['direct'],
        sourceDetail: d.detail,
        directDetail: d.detail,
        checkError: false,
      });
    }
  }

  ensureAllDeliveryRetailers(map, directCheckEnabled);

  return [...map.values()].sort((a, b) => a.retailerName.localeCompare(b.retailerName));
}
