// Geometry shared by every chart: scales, ticks, ribbon paths and the map projection.
import type { Airport, CompactPoint, Verdict } from "./types";

export const linear = (d0: number, d1: number, r0: number, r1: number) =>
  (v: number) => (d1 === d0 ? (r0 + r1) / 2 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0));

export function bounds(values: number[], pad = 0.12): [number, number] {
  const lo = Math.min(...values), hi = Math.max(...values);
  const span = Math.max(hi - lo, Math.abs(hi) * 0.01, 1e-6);
  return [lo - span * pad, hi + span * pad];
}

export function niceTicks(lo: number, hi: number, n = 3): number[] {
  const raw = (hi - lo) / Math.max(n, 1);
  if (raw <= 0) return [lo];
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6));
  return out;
}

/** 0..4 on the diverging scale, against a typical band. 2 = inside the band. */
export function levelIndex(value: number, low: number | null, high: number | null): number {
  if (low == null || high == null) return 2;
  const spread = Math.max(high - low, 1e-9);
  if (value > high) return value > high + spread ? 4 : 3;
  if (value < low) return value < low - spread ? 0 : 1;
  return 2;
}

export const LEVEL_COLORS = ["var(--r-cool-2)", "var(--r-cool-1)", "var(--r-even)",
  "var(--r-warm-1)", "var(--r-warm-2)"];

export interface RibbonGeometry {
  line: string;
  area: string;
  band: { y: number; h: number } | null;
  stops: { offset: number; color: string }[];
  x: (i: number) => number;
  y: (v: number) => number;
  domain: [number, number];
}

/** Paths for the fare ribbon in a w × h box. Colour follows a centred 5-day median so one
 *  noisy day does not flip it; the line itself is never smoothed. */
export function ribbonGeometry(points: CompactPoint[], typical: Pick<Verdict, "usual_low" | "usual_high"> | null,
                               w: number, h: number): RibbonGeometry {
  const values = points.map((p) => p[1]);
  const lows = points.map((p) => p[2] ?? p[1]);
  const highs = points.map((p) => p[3] ?? p[1]);
  const extra = [typical?.usual_low, typical?.usual_high].filter((v): v is number => v != null);
  const domain = bounds([...lows, ...highs, ...extra]);
  const x = linear(0, Math.max(points.length - 1, 1), 0, w);
  const y = linear(domain[0], domain[1], h, 0);
  const minHalf = h * 0.012;
  const up = points.map((p, i) => [x(i), Math.min(y(highs[i]), y(p[1]) - minHalf)]);
  const down = points.map((p, i) => [x(i), Math.max(y(lows[i]), y(p[1]) + minHalf)]);
  const f = (n: number) => n.toFixed(1);
  const area = `M${up.map(([a, b]) => `${f(a)},${f(b)}`).join(" L")} L${down.reverse()
    .map(([a, b]) => `${f(a)},${f(b)}`).join(" L")} Z`;
  const line = `M${points.map((p, i) => `${f(x(i))},${f(y(p[1]))}`).join(" L")}`;
  const lo = typical?.usual_low ?? null, hi = typical?.usual_high ?? null;
  const stops = values.map((_, i) => {
    const win = values.slice(Math.max(0, i - 2), i + 3).sort((a, b) => a - b);
    return { offset: (x(i) / w) * 100, color: LEVEL_COLORS[levelIndex(win[win.length >> 1], lo, hi)] };
  });
  const band = lo != null && hi != null ? { y: y(hi), h: Math.max(y(lo) - y(hi), 0.5) } : null;
  return { line, area, band, stops, x, y, domain };
}

export function linePath(xs: number[], ys: number[]): string {
  return xs.map((x, i) => `${i ? "L" : "M"}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(" ");
}

// ---------------------------------------------------------------------- the route chart

export const CHART_SCALE = 26;     // viewBox units per degree of latitude
export const CHART_MARGIN = 30;

export interface Projection {
  lat0: number; lat1: number; lon0: number; lon1: number;
  width: number; height: number;
  xy: (lat: number, lon: number) => [number, number];
}

/** Equirectangular, scaled by cos(mid-latitude), framed on whole degrees. */
export function projection(airports: Airport[]): Projection {
  const lats = airports.map((a) => a.lat), lons = airports.map((a) => a.lon);
  const lat0 = Math.floor(Math.min(...lats)) - 1, lat1 = Math.ceil(Math.max(...lats)) + 1;
  const lon0 = Math.floor(Math.min(...lons)) - 1, lon1 = Math.ceil(Math.max(...lons)) + 2;
  const k = Math.cos(((lat0 + lat1) / 2) * (Math.PI / 180));
  return {
    lat0, lat1, lon0, lon1,
    width: (lon1 - lon0) * k * CHART_SCALE,
    height: (lat1 - lat0) * CHART_SCALE,
    xy: (lat, lon) => [CHART_MARGIN + (lon - lon0) * k * CHART_SCALE,
                       CHART_MARGIN + (lat1 - lat) * CHART_SCALE],
  };
}

/** The directed lane o→d: offset to one side of the city-pair line, stopped short of the
 *  airport symbols, so the two directions of a pair read as two lanes. */
export function lane(p: Projection, a: Airport, b: Airport, side = 1.9, cut = 5.5) {
  const [x0, y0] = p.xy(a.lat, a.lon), [x1, y1] = p.xy(b.lat, b.lon);
  const len = Math.hypot(x1 - x0, y1 - y0) || 1;
  const ux = (x1 - x0) / len, uy = (y1 - y0) / len;
  const s = a.iata < b.iata ? side : -side;
  return {
    x0: x0 - uy * s + ux * cut, y0: y0 + ux * s + uy * cut,
    x1: x1 - uy * s - ux * cut, y1: y1 + ux * s - uy * cut,
    angle: Math.atan2(y1 - y0, x1 - x0) * (180 / Math.PI),
    normal: [-uy * Math.sign(s), ux * Math.sign(s)] as [number, number],
  };
}

export function greatCircleKm(a: Airport, b: Airport): number {
  const r = Math.PI / 180;
  const dp = (b.lat - a.lat) * r, dl = (b.lon - a.lon) * r;
  const h = Math.sin(dp / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dl / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
