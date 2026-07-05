import AsyncStorage from '@react-native-async-storage/async-storage';

import { AppSettings, DEFAULT_SETTINGS } from '../types';

const SETTINGS_KEY = 'portasplit.settings';
const ALERTED_KEY = 'portasplit.alerted';

type StoredSettings = Partial<AppSettings> & { cloudMonitorEnabled?: boolean };

function migrateSettings(parsed: StoredSettings): AppSettings {
  const merged: AppSettings = { ...DEFAULT_SETTINGS, ...parsed };

  if (parsed.cloudMonitorEnabled !== undefined && parsed.forceLocalCheck === undefined) {
    merged.forceLocalCheck = !parsed.cloudMonitorEnabled;
  }

  return merged;
}

export async function loadSettings(): Promise<AppSettings> {
  try {
    const raw = await AsyncStorage.getItem(SETTINGS_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS };
    return migrateSettings(JSON.parse(raw) as StoredSettings);
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

export async function loadAlertedKeys(): Promise<Set<string>> {
  try {
    const raw = await AsyncStorage.getItem(ALERTED_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set();
  }
}

export async function saveAlertedKeys(keys: Set<string>): Promise<void> {
  await AsyncStorage.setItem(ALERTED_KEY, JSON.stringify([...keys]));
}
