import { useEffect, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { CLOUD_MONITOR_INTERVAL_MIN } from '@/src/constants/cloudMonitor';
import { allowedDepartments, departmentLabel } from '@/src/constants/departments';
import {
  backgroundFetchStatusLabel,
  registerBackgroundFetch,
} from '@/src/services/backgroundFetch';
import { notifyTest, requestNotificationPermissions } from '@/src/services/notifications';
import { loadSettings, saveSettings } from '@/src/services/settings';
import type { AppSettings } from '@/src/types';
import { DEFAULT_SETTINGS } from '@/src/types';

export default function SettingsScreen() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [saved, setSaved] = useState<string | null>(null);
  const [bgStatus, setBgStatus] = useState<string>('…');

  useEffect(() => {
    loadSettings().then(setSettings);
    backgroundFetchStatusLabel().then(setBgStatus);
  }, []);

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(null);
  };

  const depts = [...allowedDepartments(settings.postalCode)].map(departmentLabel);

  const onSave = async () => {
    await saveSettings(settings);
    await registerBackgroundFetch();
    const status = await backgroundFetchStatusLabel();
    setBgStatus(status);
    setSaved('Réglages enregistrés');
  };

  const onTestNotification = async () => {
    await requestNotificationPermissions();
    await notifyTest(settings.postalCode, 0);
    setSaved('Notification de test envoyée');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <Text style={styles.title}>Localisation</Text>
        <Text style={styles.label}>Code postal</Text>
        <TextInput
          style={styles.input}
          value={settings.postalCode}
          onChangeText={(v) => update('postalCode', v)}
          keyboardType="number-pad"
          maxLength={5}
        />
        <Text style={styles.label}>Rayon : {settings.radiusKm} km</Text>
        <View style={styles.stepper}>
          <Pressable
            style={styles.stepBtn}
            onPress={() => update('radiusKm', Math.max(10, settings.radiusKm - 10))}>
            <Text style={styles.stepBtnText}>−</Text>
          </Pressable>
          <Pressable
            style={styles.stepBtn}
            onPress={() => update('radiusKm', Math.min(300, settings.radiusKm + 10))}>
            <Text style={styles.stepBtnText}>+</Text>
          </Pressable>
        </View>
        <Text style={styles.hint}>
          Départements suivis : {depts.join(', ')}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.title}>Moniteur cloud</Text>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Utiliser GitHub Actions (Telegram)</Text>
          <Switch
            value={settings.cloudMonitorEnabled}
            onValueChange={(v) => update('cloudMonitorEnabled', v)}
          />
        </View>
        <Text style={styles.hint}>
          Lit le snapshot publie toutes les {CLOUD_MONITOR_INTERVAL_MIN} min — meme source que
          les alertes Telegram. Fallback local si indisponible.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.title}>Vérifications locales</Text>
        <Text style={styles.label}>
          Intervalle (app ouverte) : {settings.intervalMinutes} min
        </Text>
        <View style={styles.stepper}>
          <Pressable
            style={styles.stepBtn}
            onPress={() => update('intervalMinutes', Math.max(1, settings.intervalMinutes - 1))}>
            <Text style={styles.stepBtnText}>−</Text>
          </Pressable>
          <Pressable
            style={styles.stepBtn}
            onPress={() => update('intervalMinutes', Math.min(30, settings.intervalMinutes + 1))}>
            <Text style={styles.stepBtnText}>+</Text>
          </Pressable>
        </View>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Double vérification avant alerte</Text>
          <Switch value={settings.confirmStock} onValueChange={(v) => update('confirmStock', v)} />
        </View>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Utiliser ClimRadar (si disponible)</Text>
          <Switch
            value={settings.climradarEnabled}
            onValueChange={(v) => update('climradarEnabled', v)}
          />
        </View>
        <Text style={styles.hint}>
          Agrégateur ClimRadar (API JSON, MAJ ~10 min). Fallback autonome si indisponible.
        </Text>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Vérification directe des sites revendeurs</Text>
          <Switch
            value={settings.directCheckEnabled}
            onValueChange={(v) => update('directCheckEnabled', v)}
          />
        </View>
        <Text style={styles.hint}>
          Interroge Amazon, Boulanger, Castorama, etc. directement — source principale en mode
          autonome.
        </Text>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Afficher les magasins en rupture</Text>
          <Switch
            value={settings.showOutOfStock}
            onValueChange={(v) => update('showOutOfStock', v)}
          />
        </View>
        <View style={styles.switchRow}>
          <Text style={styles.label}>Actualisation en arrière-plan</Text>
          <Switch
            value={settings.backgroundFetchEnabled}
            onValueChange={(v) => update('backgroundFetchEnabled', v)}
          />
        </View>
        <Text style={styles.hint}>
          Arrière-plan : iOS réveille l’app environ toutes les 15–60 min (pas garanti).
          État iOS : {bgStatus}
        </Text>
      </View>

      <Pressable style={styles.primaryBtn} onPress={onSave}>
        <Text style={styles.primaryBtnText}>Enregistrer</Text>
      </Pressable>

      <Pressable style={styles.secondaryBtn} onPress={onTestNotification}>
        <Text style={styles.secondaryBtnText}>Test notification</Text>
      </Pressable>

      {saved && <Text style={styles.saved}>{saved}</Text>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  content: { padding: 16, gap: 12, paddingBottom: 32 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    gap: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  title: { fontSize: 18, fontWeight: '700', color: '#0f172a' },
  label: { fontSize: 15, color: '#334155' },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f8fafc',
  },
  stepper: { flexDirection: 'row', gap: 12 },
  stepBtn: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: '#e2e8f0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepBtnText: { fontSize: 22, fontWeight: '700', color: '#0f172a' },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  hint: { color: '#64748b', fontSize: 13, lineHeight: 18 },
  primaryBtn: {
    backgroundColor: '#2563eb',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  primaryBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  secondaryBtn: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#cbd5e1',
  },
  secondaryBtnText: { color: '#2563eb', fontWeight: '600', fontSize: 16 },
  saved: { color: '#16a34a', textAlign: 'center', fontWeight: '600' },
});
