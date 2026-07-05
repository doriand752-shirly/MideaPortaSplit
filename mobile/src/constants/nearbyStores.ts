/** Magasins physiques connus (zone Gironde + départements frontaliers). */

export interface NearbyStoreDef {
  id: string;
  retailerId: 'leroy_merlin' | 'castorama' | 'boulanger' | 'darty';
  name: string;
  city: string;
  postalCode: string;
  /** Castorama — ID pour /store/{id}/produit */
  castoramaStoreId?: string;
  /** Leroy Merlin — slug magasin (?store=slug) */
  lmStoreSlug?: string;
  /** Boulanger — code site (API promise) */
  boulangerSiteCode?: string;
}

export const NEARBY_STORES: NearbyStoreDef[] = [
  // Gironde (33)
  { id: 'lm-merignac', retailerId: 'leroy_merlin', name: 'Leroy Merlin Mérignac', city: 'Mérignac', postalCode: '33700', lmStoreSlug: 'merignac-bordeaux' },
  { id: 'lm-gradignan', retailerId: 'leroy_merlin', name: 'Leroy Merlin Gradignan', city: 'Gradignan', postalCode: '33170', lmStoreSlug: 'gradignan-bordeaux' },
  { id: 'lm-bordeaux-lac', retailerId: 'leroy_merlin', name: 'Leroy Merlin Bordeaux Lac', city: 'Bordeaux', postalCode: '33300', lmStoreSlug: 'bordeaux-lac' },
  { id: 'lm-pessac', retailerId: 'leroy_merlin', name: 'Leroy Merlin Pessac', city: 'Pessac', postalCode: '33600', lmStoreSlug: 'pessac' },
  { id: 'lm-libourne', retailerId: 'leroy_merlin', name: 'Leroy Merlin Libourne', city: 'Libourne', postalCode: '33500', lmStoreSlug: 'libourne' },
  { id: 'lm-arcachon', retailerId: 'leroy_merlin', name: 'Leroy Merlin Arcachon', city: 'La Teste-de-Buch', postalCode: '33260', lmStoreSlug: 'arcachon' },
  { id: 'ca-merignac', retailerId: 'castorama', name: 'Castorama Mérignac', city: 'Mérignac', postalCode: '33700', castoramaStoreId: '1488' },
  { id: 'ca-begles', retailerId: 'castorama', name: 'Castorama Bègles', city: 'Bègles', postalCode: '33130', castoramaStoreId: '1059' },
  { id: 'ca-bordeaux', retailerId: 'castorama', name: 'Castorama Bordeaux', city: 'Bordeaux', postalCode: '33300', castoramaStoreId: '0174' },
  { id: 'bo-bordeaux', retailerId: 'boulanger', name: 'Boulanger Bordeaux', city: 'Bordeaux', postalCode: '33000' },
  { id: 'bo-merignac', retailerId: 'boulanger', name: 'Boulanger Mérignac', city: 'Mérignac', postalCode: '33700' },
  { id: 'bo-pessac', retailerId: 'boulanger', name: 'Boulanger Pessac', city: 'Pessac', postalCode: '33600' },
  { id: 'da-bordeaux', retailerId: 'darty', name: 'Darty Bordeaux', city: 'Bordeaux', postalCode: '33000' },
  { id: 'da-merignac', retailerId: 'darty', name: 'Darty Mérignac', city: 'Mérignac', postalCode: '33700' },
  // Charente-Maritime (17)
  { id: 'lm-la-rochelle', retailerId: 'leroy_merlin', name: 'Leroy Merlin La Rochelle', city: 'Puilboreau', postalCode: '17138', lmStoreSlug: 'la-rochelle' },
  { id: 'lm-saintes', retailerId: 'leroy_merlin', name: 'Leroy Merlin Saintes', city: 'Saintes', postalCode: '17100', lmStoreSlug: 'saintes' },
  { id: 'ca-la-rochelle', retailerId: 'castorama', name: 'Castorama La Rochelle', city: 'Puilboreau', postalCode: '17138', castoramaStoreId: '1289' },
  { id: 'bo-la-rochelle', retailerId: 'boulanger', name: 'Boulanger La Rochelle', city: 'La Rochelle', postalCode: '17000' },
  // Charente (16)
  { id: 'lm-angouleme', retailerId: 'leroy_merlin', name: 'LM Soyaux – Angoulême – Cognac', city: 'Soyaux', postalCode: '16800', lmStoreSlug: 'soyaux-angouleme-cognac' },
  { id: 'ca-angouleme', retailerId: 'castorama', name: 'Castorama Angoulême', city: 'Champniers', postalCode: '16430', castoramaStoreId: '1374' },
  // Landes (40)
  { id: 'lm-mont-de-marsan', retailerId: 'leroy_merlin', name: 'Leroy Merlin Mont-de-Marsan', city: 'Saint-Pierre-du-Mont', postalCode: '40280', lmStoreSlug: 'mont-de-marsan' },
  { id: 'lm-dax', retailerId: 'leroy_merlin', name: 'Leroy Merlin Dax', city: 'Saint-Paul-lès-Dax', postalCode: '40990', lmStoreSlug: 'dax' },
  // Dordogne (24)
  { id: 'lm-perigueux', retailerId: 'leroy_merlin', name: 'Leroy Merlin Périgueux', city: 'Boulazac', postalCode: '24750', lmStoreSlug: 'perigueux' },
  { id: 'ca-perigueux', retailerId: 'castorama', name: 'Castorama Périgueux', city: 'Périgueux', postalCode: '24000', castoramaStoreId: '1412' },
  // Lot-et-Garonne (47)
  { id: 'lm-agen', retailerId: 'leroy_merlin', name: 'Leroy Merlin Agen', city: 'Agen', postalCode: '47000', lmStoreSlug: 'agen' },
  // Pyrénées-Atlantiques (64)
  { id: 'lm-pau', retailerId: 'leroy_merlin', name: 'Leroy Merlin Pau', city: 'Lescar', postalCode: '64230', lmStoreSlug: 'pau' },
  { id: 'lm-bayonne', retailerId: 'leroy_merlin', name: 'Leroy Merlin Bayonne', city: 'Bayonne', postalCode: '64100', lmStoreSlug: 'bayonne' },
  // Deux-Sèvres (79) / Haute-Vienne (87)
  { id: 'lm-niort', retailerId: 'leroy_merlin', name: 'Leroy Merlin Niort', city: 'Niort', postalCode: '79000', lmStoreSlug: 'niort' },
  { id: 'lm-limoges', retailerId: 'leroy_merlin', name: 'Leroy Merlin Limoges', city: 'Limoges', postalCode: '87220', lmStoreSlug: 'limoges' },
];

/** Revendeurs avec retrait magasin (vérification page produit / API magasin). */
export const PICKUP_RETAILER_IDS = new Set(['leroy_merlin', 'castorama', 'boulanger', 'darty']);

/** Délai entre deux checks magasin (anti-bot). */
export const STORE_CHECK_DELAY_MS = 1400;
