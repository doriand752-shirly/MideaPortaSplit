import {
  CLOUD_SNAPSHOT_STALE_MS,
  CLOUD_SNAPSHOT_URL,
} from '../constants/cloudMonitor';
import type { MonitorSnapshot } from '../types';

function isMonitorSnapshot(value: unknown): value is MonitorSnapshot {
  if (!value || typeof value !== 'object') return false;
  const v = value as MonitorSnapshot;
  return (
    typeof v.checkedAt === 'string' &&
    Array.isArray(v.onlineOffers) &&
    Array.isArray(v.localStores) &&
    Array.isArray(v.actionable)
  );
}

export async function fetchCloudSnapshot(
  url = CLOUD_SNAPSHOT_URL,
): Promise<MonitorSnapshot | null> {
  try {
    const response = await fetch(`${url}?t=${Date.now()}`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    const json: unknown = await response.json();
    if (!isMonitorSnapshot(json)) return null;

    const ageMs = Date.now() - new Date(json.checkedAt).getTime();
    if (!Number.isFinite(ageMs) || ageMs > CLOUD_SNAPSHOT_STALE_MS) {
      return null;
    }

    return {
      ...json,
      dataMode: 'cloud',
    };
  } catch {
    return null;
  }
}

export function adaptCloudSnapshot(
  snapshot: MonitorSnapshot,
  settings: { postalCode: string; radiusKm: number; showOutOfStock: boolean },
): MonitorSnapshot {
  let errorMessage = snapshot.errorMessage;
  if (snapshot.postalCode !== settings.postalCode) {
    errorMessage = `Donnees pour ${snapshot.postalCode} (reglages: ${settings.postalCode})`;
  } else if (snapshot.radiusKm !== settings.radiusKm) {
    errorMessage = `Rayon snapshot ${snapshot.radiusKm} km (reglages: ${settings.radiusKm} km)`;
  }

  const localStores = settings.showOutOfStock
    ? snapshot.localStores
    : snapshot.localStores.filter((s) => s.inStock);

  return {
    ...snapshot,
    localStores,
    errorMessage,
  };
}
