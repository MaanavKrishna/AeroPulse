// Plain-language summaries of the national patterns, used on the home and trends pages.
import { WEEKDAY_NAMES } from "./copy";
import type { Insights, WeekdayEffect } from "./types";

/** The stretch of booking distances that sits in the cheapest fifth of the curve. */
export function cheapestStretch(curve: { days_ahead: number; value: number }[]): [number, number] | null {
  if (curve.length < 10) return null;
  const sorted = curve.map((c) => c.value).sort((a, b) => a - b);
  const cut = sorted[Math.floor((sorted.length - 1) * 0.2)];
  const cheap = curve.filter((c) => c.value <= cut).map((c) => c.days_ahead);
  return cheap.length ? [Math.min(...cheap), Math.max(...cheap)] : null;
}

export function nationalCurve(i: Insights) {
  return i.booking_curve.map((c) => ({ days_ahead: c.days_ahead, value: c.pct_vs_route_median }));
}

export function lastMinutePremium(i: Insights): number | null {
  const near = i.booking_curve.filter((c) => c.days_ahead <= 3);
  if (!near.length) return null;
  return near.reduce((s, c) => s + c.pct_vs_route_median, 0) / near.length;
}

export function weekdaySentence(days: WeekdayEffect[]): string {
  if (days.length < 5) return "Not enough data yet to compare days of the week.";
  const lo = days.reduce((a, b) => (b.pct_vs_typical < a.pct_vs_typical ? b : a));
  const hi = days.reduce((a, b) => (b.pct_vs_typical > a.pct_vs_typical ? b : a));
  return `${WEEKDAY_NAMES[lo.weekday]} departures were usually the cheapest (${lo.pct_vs_typical.toFixed(0)}% against usual), ${WEEKDAY_NAMES[hi.weekday]} the dearest (+${hi.pct_vs_typical.toFixed(0)}%).`;
}
