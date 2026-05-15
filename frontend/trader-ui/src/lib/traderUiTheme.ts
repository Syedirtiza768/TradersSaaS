/**
 * Applies per-user Trader UI preferences from settings payload (see trader_app.api.settings).
 * Called after login / checkAuth and whenever settings are saved.
 */

export interface TraderUiPrefs {
  language: string;
  time_zone: string;
  date_format: string;
  number_format: string;
  float_precision: number;
  session_expiry: number;
  enable_two_factor: number;
  dark_mode: number;
  compact_tables: number;
  email_notifications: number;
}

function asInt(v: unknown, fallback: number): number {
  const n = typeof v === 'string' ? parseInt(v, 10) : Number(v);
  return Number.isFinite(n) ? n : fallback;
}

/** Normalise API / default payload into TraderUiPrefs. */
export function normaliseUiPrefs(ui: Record<string, unknown> | null | undefined): TraderUiPrefs {
  const u = ui || {};
  return {
    language: typeof u.language === 'string' && u.language ? u.language : 'en',
    time_zone: typeof u.time_zone === 'string' && u.time_zone ? u.time_zone : 'Asia/Karachi',
    date_format: typeof u.date_format === 'string' && u.date_format ? u.date_format : 'dd-mm-yyyy',
    number_format: typeof u.number_format === 'string' && u.number_format ? u.number_format : '#,###.##',
    float_precision: asInt(u.float_precision, 3),
    session_expiry: asInt(u.session_expiry, 240),
    enable_two_factor: asInt(u.enable_two_factor, 0) ? 1 : 0,
    dark_mode: asInt(u.dark_mode, 0) ? 1 : 0,
    compact_tables: asInt(u.compact_tables, 0) ? 1 : 0,
    email_notifications: asInt(u.email_notifications, 1) ? 1 : 0,
  };
}

export function applyTraderUiTheme(ui: TraderUiPrefs | null | undefined): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  if (!ui) {
    root.classList.remove('dark');
    root.removeAttribute('data-compact-tables');
    return;
  }
  root.classList.toggle('dark', ui.dark_mode === 1);
  root.dataset.compactTables = ui.compact_tables === 1 ? '1' : '0';
}

export function clearTraderUiTheme(): void {
  applyTraderUiTheme(null);
}
