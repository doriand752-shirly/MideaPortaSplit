import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

import { notifyOffers } from './notifications';
import { loadSettings } from './settings';
import { runStockCheck } from './stockMonitor';

export const BACKGROUND_FETCH_TASK = 'portasplit-background-fetch';

/** Doit être défini au chargement du module (hors composants React). */
TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
  try {
    const settings = await loadSettings();
    if (!settings.backgroundFetchEnabled) {
      return BackgroundFetch.BackgroundFetchResult.NoData;
    }

    const { newOffers } = await runStockCheck(settings);
    if (newOffers.length > 0) {
      await notifyOffers(newOffers);
    }

    return newOffers.length > 0
      ? BackgroundFetch.BackgroundFetchResult.NewData
      : BackgroundFetch.BackgroundFetchResult.NoData;
  } catch {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

export async function backgroundFetchStatusLabel(): Promise<string> {
  const status = await BackgroundFetch.getStatusAsync();
  switch (status) {
    case BackgroundFetch.BackgroundFetchStatus.Available:
      return 'Disponible';
    case BackgroundFetch.BackgroundFetchStatus.Denied:
      return 'Refusé par iOS';
    case BackgroundFetch.BackgroundFetchStatus.Restricted:
      return 'Restreint';
    default:
      return 'Inconnu';
  }
}

export async function registerBackgroundFetch(): Promise<void> {
  const settings = await loadSettings();
  if (!settings.backgroundFetchEnabled) {
    await unregisterBackgroundFetch();
    return;
  }

  const status = await BackgroundFetch.getStatusAsync();
  if (
    status === BackgroundFetch.BackgroundFetchStatus.Restricted ||
    status === BackgroundFetch.BackgroundFetchStatus.Denied
  ) {
    return;
  }

  const intervalSec = Math.max(settings.intervalMinutes, 15) * 60;
  const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_FETCH_TASK);

  if (isRegistered) {
    await BackgroundFetch.unregisterTaskAsync(BACKGROUND_FETCH_TASK);
  }

  await BackgroundFetch.registerTaskAsync(BACKGROUND_FETCH_TASK, {
    minimumInterval: intervalSec,
    stopOnTerminate: false,
    startOnBoot: true,
  });
}

export async function unregisterBackgroundFetch(): Promise<void> {
  const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_FETCH_TASK);
  if (isRegistered) {
    await BackgroundFetch.unregisterTaskAsync(BACKGROUND_FETCH_TASK);
  }
}
