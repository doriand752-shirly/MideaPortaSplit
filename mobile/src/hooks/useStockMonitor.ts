import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, AppStateStatus } from 'react-native';

import { notifyOffers, requestNotificationPermissions } from '../services/notifications';
import { registerBackgroundFetch } from '../services/backgroundFetch';
import { loadSettings } from '../services/settings';
import { runStockCheck, type StockCheckOptions } from '../services/stockMonitor';
import type { AppSettings, MonitorSnapshot } from '../types';

export function useStockMonitor() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [snapshot, setSnapshot] = useState<MonitorSnapshot | null>(null);
  const [checking, setChecking] = useState(false);
  const [monitoring, setMonitoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const check = useCallback(
    async (currentSettings?: AppSettings, options?: StockCheckOptions) => {
      const active = currentSettings ?? settings ?? (await loadSettings());
      setChecking(true);
      setError(null);
      try {
        const { snapshot: next, newOffers } = await runStockCheck(active, options);
        setSnapshot(next);
        if (newOffers.length > 0) {
          await notifyOffers(newOffers);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      } finally {
        setChecking(false);
      }
    },
    [settings],
  );

  const checkLocalOnce = useCallback(async () => {
    const active = settings ?? (await loadSettings());
    await check(active, { forceLocal: true });
  }, [check, settings]);

  const start = useCallback(async () => {
    const loaded = await loadSettings();
    setSettings(loaded);
    setMonitoring(true);
    await requestNotificationPermissions();
    await registerBackgroundFetch();
    await check(loaded);
  }, [check]);

  const stop = useCallback(() => {
    setMonitoring(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!monitoring || !settings) return;

    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(
      () => {
        check(settings);
      },
      Math.max(settings.intervalMinutes, 1) * 60 * 1000,
    );

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [monitoring, settings, check]);

  useEffect(() => {
    const onAppState = (state: AppStateStatus) => {
      if (state === 'active' && monitoring && settings) {
        check(settings);
      }
    };
    const sub = AppState.addEventListener('change', onAppState);
    return () => sub.remove();
  }, [monitoring, settings, check]);

  return {
    settings,
    setSettings,
    snapshot,
    checking,
    monitoring,
    error,
    check,
    checkLocalOnce,
    start,
    stop,
    setMonitoring,
  };
}
