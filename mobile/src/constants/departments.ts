/** Départements frontaliers autour de la Gironde (33). */
export const BORDER_DEPARTMENTS: Record<string, readonly string[]> = {
  '33': ['33', '16', '17', '24', '40', '47', '64', '79', '87'],
};

export const BORDER_DEPARTMENT_LABELS: Record<string, string> = {
  '33': 'Gironde',
  '16': 'Charente',
  '17': 'Charente-Maritime',
  '24': 'Dordogne',
  '40': 'Landes',
  '47': 'Lot-et-Garonne',
  '64': 'Pyrénées-Atlantiques',
  '79': 'Deux-Sèvres',
  '87': 'Haute-Vienne',
};

export function allowedDepartments(postalCode: string): Set<string> {
  const dept = postalCode.slice(0, 2);
  const border = BORDER_DEPARTMENTS[dept];
  return new Set(border ?? [dept]);
}

export function departmentLabel(dept: string): string {
  return BORDER_DEPARTMENT_LABELS[dept] ?? `Dép. ${dept}`;
}
