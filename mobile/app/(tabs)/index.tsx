import { Ionicons } from '@expo/vector-icons';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { departmentLabel } from '@/src/constants/departments';
import { useStockMonitor } from '@/src/hooks/useStockMonitor';
import { formatLastUpdate, type LocalStoreOffer } from '@/src/types';

type TabKey = 'action' | 'stores' | 'online';

export default function StockScreen() {
  const { snapshot, checking, monitoring, error, check, start, stop } = useStockMonitor();
  const [tab, setTab] = useState<TabKey>('action');

  useEffect(() => {
    start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const actionable = snapshot?.actionable ?? [];
  const localStores = snapshot?.localStores ?? [];
  const online = snapshot?.onlineOffers ?? [];

  const storesByDept = useMemo(() => {
    const groups = new Map<string, LocalStoreOffer[]>();
    for (const store of localStores) {
      const key = store.department;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(store);
    }
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [localStores]);

  const inStockCount = localStores.filter((s) => s.inStock).length;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={checking} onRefresh={() => check()} />}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Surveillance</Text>
        <Row label="État" value={monitoring ? 'Active' : 'En pause'} highlight={monitoring} />
        {snapshot && (
          <>
            <Row label="Zone" value={`${snapshot.postalCode} · ${snapshot.radiusKm} km`} />
            <Row
              label="Départements"
              value={snapshot.monitoredDepartments?.join(', ') ?? '—'}
            />
            <Row
              label="Dernière vérif"
              value={new Date(snapshot.checkedAt).toLocaleString('fr-FR')}
            />
            <Row
              label="Source données"
              value={
                snapshot.dataMode === 'independent'
                  ? 'Autonome (sites revendeurs)'
                  : snapshot.dataMode === 'climradar'
                    ? 'ClimRadar'
                    : 'Hybride'
              }
            />
          </>
        )}
        {snapshot?.dataMode === 'independent' && (
          <Text style={styles.hint}>
            ClimRadar indisponible — l’app interroge directement les sites revendeurs.
          </Text>
        )}
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Pressable
          style={[styles.button, monitoring ? styles.buttonSecondary : styles.buttonPrimary]}
          onPress={() => (monitoring ? stop() : start())}>
          <Text style={styles.buttonText}>{monitoring ? 'Pause' : 'Démarrer'}</Text>
        </Pressable>
      </View>

      <View style={styles.tabs}>
        {(
          [
            ['action', `Action (${actionable.length})`],
            ['stores', `Magasins (${inStockCount}/${localStores.length})`],
            ['online', `En ligne (${online.length})`],
          ] as const
        ).map(([key, label]) => (
          <Pressable
            key={key}
            style={[styles.tab, tab === key && styles.tabActive]}
            onPress={() => setTab(key)}>
            <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>{label}</Text>
          </Pressable>
        ))}
      </View>

      {tab === 'action' && (
        <View style={styles.card}>
          {actionable.length === 0 ? (
            <Text style={styles.muted}>Rien d’actionnable pour l’instant</Text>
          ) : (
            actionable.map((offer) => (
              <Pressable
                key={offer.id}
                style={styles.offer}
                onPress={() => Linking.openURL(offer.url)}>
                <View style={styles.offerHeader}>
                  <Text style={styles.offerTitle}>{offer.title}</Text>
                  <Badge
                    label={offer.kind === 'magasin' ? 'Magasin' : 'Livraison'}
                    tone={offer.kind === 'magasin' ? 'green' : 'blue'}
                  />
                </View>
                <Text style={styles.muted}>{offer.detail}</Text>
                {offer.price != null && <Text style={styles.price}>{offer.price} €</Text>}
                <Text style={styles.link}>Ouvrir la page produit →</Text>
              </Pressable>
            ))
          )}
        </View>
      )}

      {tab === 'stores' && (
        <View style={styles.card}>
          {localStores.length === 0 ? (
            <Text style={styles.muted}>Aucun magasin dans la zone</Text>
          ) : (
            storesByDept.map(([dept, stores]) => (
              <View key={dept} style={styles.deptGroup}>
                <Text style={styles.deptTitle}>
                  {departmentLabel(dept)} ({stores.filter((s) => s.inStock).length}/{stores.length})
                </Text>
                {stores.map((store) => (
                  <Pressable
                    key={store.id}
                    style={[styles.storeRow, store.inStock && styles.storeRowStock]}
                    onPress={() => Linking.openURL(store.productURL)}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.offerTitle}>{store.storeName}</Text>
                      <Text style={styles.muted}>
                        {store.location} · {store.distanceKm} km
                      </Text>
                      <Text style={styles.meta}>
                        {store.inStock ? 'En stock' : store.stockSource === 'unknown' ? 'Inconnu' : 'Rupture'}
                        {store.stockSource === 'direct_store' ? ' (magasin)' : ''}
                        {store.price != null ? ` · ${store.price} €` : ''}
                        {' · '}
                        {formatLastUpdate(store.lastUpdateMin)}
                      </Text>
                      {store.stockNote ? (
                        <Text style={styles.hint}>{store.stockNote}</Text>
                      ) : null}
                    </View>
                    <Ionicons
                      name={store.inStock ? 'checkmark-circle' : 'close-circle-outline'}
                      size={24}
                      color={store.inStock ? '#16a34a' : '#94a3b8'}
                    />
                  </Pressable>
                ))}
              </View>
            ))
          )}
          <Text style={styles.hint}>
            {snapshot?.dataMode === 'independent'
              ? 'Castorama : API Kingfisher (50 magasins/appel). LM : endpoint stock officiel — peut être bloqué sans session navigateur.'
              : 'Certains magasins (ex. LM Soyaux–Angoulême) peuvent manquer si ClimRadar ne les référence pas encore.'}
          </Text>
        </View>
      )}

      {tab === 'online' && (
        <View style={styles.card}>
          {online.length === 0 ? (
            <Text style={styles.muted}>Aucune offre en ligne suivie</Text>
          ) : (
            online.map((item) => (
              <Pressable
                key={item.id}
                style={[
                  styles.storeRow,
                  item.inStock && !item.checkError && styles.storeRowStock,
                  item.checkError && styles.storeRowError,
                ]}
                onPress={() => item.url && Linking.openURL(item.url)}>
                <View style={{ flex: 1 }}>
                  <View style={styles.offerHeader}>
                    <Text style={styles.offerTitle}>{item.retailerName}</Text>
                    <SourceBadges sources={item.sources} checkError={item.checkError} />
                  </View>
                  <Text style={styles.meta}>
                    {item.checkError
                      ? 'Inaccessible'
                      : item.inStock
                        ? 'En stock en ligne'
                        : 'Rupture'}
                    {item.price != null ? ` · ${item.price} €` : ''}
                    {item.deliveryEligible ? ' · Livraison OK' : ''}
                  </Text>
                  {item.sourceDetail ? (
                    <Text style={styles.hint}>{item.sourceDetail}</Text>
                  ) : null}
                </View>
                <Ionicons name="open-outline" size={22} color="#2563eb" />
              </Pressable>
            ))
          )}
        </View>
      )}

      {checking && !snapshot && (
        <ActivityIndicator size="large" color="#2563eb" style={{ marginTop: 24 }} />
      )}
    </ScrollView>
  );
}

function Row({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <View style={styles.rowItem}>
      <Text style={styles.muted}>{label}</Text>
      <Text style={[styles.rowValue, highlight && { color: '#16a34a' }]} numberOfLines={2}>
        {value}
      </Text>
    </View>
  );
}

function Badge({ label, tone }: { label: string; tone: 'green' | 'blue' | 'purple' | 'gray' | 'orange' }) {
  const toneStyle =
    tone === 'green'
      ? styles.badgeGreen
      : tone === 'blue'
        ? styles.badgeBlue
        : tone === 'purple'
          ? styles.badgePurple
          : tone === 'orange'
            ? styles.badgeOrange
            : styles.badgeGray;
  const textStyle =
    tone === 'green'
      ? styles.badgeTextGreen
      : tone === 'blue'
        ? styles.badgeTextBlue
        : tone === 'purple'
          ? styles.badgeTextPurple
          : tone === 'orange'
            ? styles.badgeTextOrange
            : styles.badgeTextGray;
  return (
    <View style={[styles.badge, toneStyle]}>
      <Text style={[styles.badgeText, textStyle]}>{label}</Text>
    </View>
  );
}

function SourceBadges({
  sources,
  checkError,
}: {
  sources?: ('climradar' | 'direct')[];
  checkError?: boolean;
}) {
  if (checkError) return <Badge label="Inaccessible" tone="orange" />;
  if (!sources?.length) return null;
  const both = sources.includes('climradar') && sources.includes('direct');
  if (both) return <Badge label="ClimRadar + Site" tone="purple" />;
  if (sources.includes('direct')) return <Badge label="Site" tone="blue" />;
  return <Badge label="ClimRadar" tone="gray" />;
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
  cardTitle: { fontSize: 18, fontWeight: '700', color: '#0f172a', marginBottom: 4 },
  tabs: { flexDirection: 'row', gap: 8 },
  tab: {
    flex: 1,
    backgroundColor: '#e2e8f0',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  tabActive: { backgroundColor: '#2563eb' },
  tabText: { fontSize: 12, fontWeight: '600', color: '#475569' },
  tabTextActive: { color: '#fff' },
  rowItem: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, paddingVertical: 4 },
  rowValue: { fontWeight: '600', color: '#0f172a', flex: 1, textAlign: 'right' },
  offer: {
    gap: 4,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  offerHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  offerTitle: { fontSize: 16, fontWeight: '600', color: '#0f172a', flex: 1 },
  price: { fontSize: 15, fontWeight: '600', color: '#2563eb' },
  link: { color: '#2563eb', fontWeight: '600', marginTop: 4 },
  muted: { color: '#64748b', fontSize: 14 },
  meta: { color: '#64748b', fontSize: 12, marginTop: 2 },
  error: { color: '#dc2626', fontSize: 14 },
  hint: { color: '#64748b', fontSize: 12, lineHeight: 17, marginTop: 8 },
  button: { marginTop: 8, borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  buttonPrimary: { backgroundColor: '#2563eb' },
  buttonSecondary: { backgroundColor: '#64748b' },
  buttonText: { color: '#fff', fontWeight: '700' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999 },
  badgeGreen: { backgroundColor: '#dcfce7' },
  badgeBlue: { backgroundColor: '#dbeafe' },
  badgePurple: { backgroundColor: '#ede9fe' },
  badgeOrange: { backgroundColor: '#ffedd5' },
  badgeGray: { backgroundColor: '#f1f5f9' },
  badgeText: { fontSize: 11, fontWeight: '600' },
  badgeTextGreen: { color: '#15803d' },
  badgeTextBlue: { color: '#1d4ed8' },
  badgeTextPurple: { color: '#6d28d9' },
  badgeTextOrange: { color: '#c2410c' },
  badgeTextGray: { color: '#475569' },
  deptGroup: { gap: 4, marginBottom: 12 },
  deptTitle: { fontSize: 14, fontWeight: '700', color: '#334155', marginBottom: 4 },
  storeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#f1f5f9',
  },
  storeRowStock: { backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' },
  storeRowError: { backgroundColor: '#fff7ed', borderColor: '#fed7aa' },
});
