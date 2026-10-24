// Numbers and dates the way an Indian reader expects them.

const inrFmt = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** 124500 → "1,24,500" */
export const inr = (v: number) => inrFmt.format(Math.round(v));
/** 124500 → "₹1,24,500" */
export const rupees = (v: number) => `₹${inr(v)}`;

/** "2026-10-24" → "24 Oct" (dates are IST calendar days; never shifted by time zone) */
export function dayMonth(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]}`;
}

export function dayMonthYear(iso: string): string {
  return `${dayMonth(iso)} ${iso.slice(0, 4)}`;
}

export function monthName(iso: string): string {
  return MONTHS[Number(iso.slice(5, 7)) - 1];
}

export function weekdayOf(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  return (new Date(Date.UTC(y, m - 1, d)).getUTCDay() + 6) % 7;   // Monday = 0
}

export function daysBetween(a: string, b: string): number {
  const t = (s: string) => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  return Math.round((t(b) - t(a)) / 86_400_000);
}

export const pct = (v: number | null | undefined, digits = 0) =>
  v == null ? "" : `${Math.abs(v).toFixed(digits)}%`;

export const signedPct = (v: number | null | undefined, digits = 1) =>
  v == null ? "" : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(digits)}%`;

export const routeSlug = (route: string) => route.toLowerCase();
