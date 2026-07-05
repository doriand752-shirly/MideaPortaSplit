/** Identifiants produit PortaSplit par enseigne. */

export const BOULANGER_SKU = '1216685';
export const CASTORAMA_EAN = '8431312260509';
export const CASTORAMA_PRODUCT_PATH =
  'climatiseur-split-midea-reversible-3500w/8431312260509_CAFR.prd';
export const LM_PRODUCT_ID = '93857579';

export const CASTORAMA_FULFILMENT_API =
  'https://www.castorama.fr/casto-browse-mfe/api/fulfilment-options';

/** Extrait les compositeOfferId depuis la page produit Castorama. */
export function extractCastoramaCompositeOfferIds(html: string): string[] {
  const ids = new Set<string>();
  const re = new RegExp(`${CASTORAMA_EAN}_[0-9]{2}c`, 'g');
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) !== null) ids.add(m[0]);
  if (!ids.size) ids.add(`${CASTORAMA_EAN}_01c`);
  return [...ids];
}
