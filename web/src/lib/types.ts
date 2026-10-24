// Shapes returned by the AeroPulse API (/v1). Kept in one place so a change to the API
// shows up as a type error everywhere it matters.

export type DataMode = "live" | "demo" | "empty";
export type Level = "above" | "typical" | "below" | "unknown";

/** [date, value, ci95_low, ci95_high] */
export type CompactPoint = [string, number, number | null, number | null];

export interface Verdict {
  level: Level;
  headline: string;
  value: number | null;
  usual_low: number | null;
  usual_high: number | null;
  usual_median: number | null;
  pct_vs_usual: number | null;
  history_days: number;
  as_of: string | null;
}

export interface Window {
  key: string;
  label: string;
  short: string;
  first_day: number;
  last_day: number;
}

export interface Meta {
  data_mode: DataMode;
  methodology_version: string;
  routes: string[];
  windows: Window[];
  latest_date: string | null;
  first_date: string | null;
  history_days: number;
  early_series: boolean;
  last_collection: { provider: string; date: string; status: string } | null;
}

export interface Airport {
  iata: string;
  icao: string;
  city: string;
  city_hi: string;
  airport: string;
  state: string;
  lat: number;
  lon: number;
  aliases?: string[];
  routes_from?: string[];
  routes_to?: string[];
}

export interface RouteRow {
  route: string;
  name: string;
  origin: string;
  destination: string;
  origin_city: string;
  destination_city: string;
  distance_km: number;
  verdict: Verdict;
  index: number | null;
  series: CompactPoint[];
}

export interface RouteWindow {
  window: string;
  label: string;
  short: string;
  verdict: Verdict;
  median_cheapest_fare_inr: number | null;
  lowest_inr: number | null;
  highest_inr: number | null;
  departure_dates_priced: number | null;
  date: string | null;
}

export interface WeekdayEffect {
  weekday: string;
  pct_vs_typical: number;
  fares: number;
}

export interface RouteDetail {
  data_mode: DataMode;
  route: string;
  name: string;
  origin: Airport;
  destination: Airport;
  distance_km: number;
  reverse: string | null;
  windows: RouteWindow[];
  index: { verdict: Verdict; series: CompactPoint[] };
  booking_curve: { days_ahead: number; median_inr: number; fares: number }[];
  usually_cheapest_days_ahead: [number, number] | null;
  weekdays: WeekdayEffect[];
}

export interface RouteFares {
  data_mode: DataMode;
  route: string;
  window: string;
  verdict: Verdict;
  latest: {
    date: string;
    median_inr: number;
    lowest_inr: number;
    highest_inr: number;
    departure_dates_priced: number;
  } | null;
  points: CompactPoint[];
}

export interface CalendarDay {
  date: string;
  level: Level;
  window: string | null;
  fare_inr: number | null;
}

export interface RouteCalendar {
  route: string;
  as_of: string | null;
  show_prices: boolean;
  days: CalendarDay[];
}

export interface Mover {
  route_id: string;
  name: string;
  change_pct: number;
  from: string;
  to: string;
}

export interface Insights {
  data_mode: DataMode;
  national: {
    verdict: Verdict;
    series: CompactPoint[];
    change_30d_pct: number | null;
    early_series: boolean;
    history_days: number;
  };
  windows: (Window & { verdict: Verdict; series: CompactPoint[] })[];
  movers: { lag_days: number; up: Mover[]; down: Mover[] };
  booking_curve: { days_ahead: number; pct_vs_route_median: number }[];
  weekdays: WeekdayEffect[];
}

export interface Festival {
  slug: string;
  name: string;
  date: string;
  date_confirmed: boolean;
  routes: string[];
}

export interface FestivalDetail {
  slug: string;
  festival: string;
  date: string;
  date_confirmed: boolean;
  peak_departure: string;
  show_prices: boolean;
  routes: {
    route: string;
    name: string;
    points: { date: string; days_ahead: number; pct_vs_ordinary: number | null; fare_inr?: number }[];
  }[];
}

export interface AirportDetail {
  data_mode: DataMode;
  airport: Airport;
  departures: RouteRow[];
  arrivals: RouteRow[];
}

export interface Methodology {
  version: string;
  windows: Window[];
  base_days: number;
  min_dates_per_product_day: number;
  price_floor_inr: number;
  price_ceiling_inr: number;
  outlier_z: number;
  coverage_publish_pct: number;
  coverage_warn_pct: number;
  se_replications: number;
  se_seed: number;
  typical_lookback_days: number;
  typical_low_pct: number;
  typical_high_pct: number;
  min_history_for_verdict: number;
  early_series_days: number;
  exclusion_reasons: Record<string, string>;
  weights: { basket_version: string; route: string; weight: number; source: string;
             base_from: string | null; base_to: string | null }[];
  links: { series: string; from_version: string; to_version: string; link_date: string;
           factor: number }[];
}

export interface Sources {
  providers: { name: string; display_name: string; homepage: string; kind: string;
               terms_reviewed: boolean; raw_redistribution: boolean; attribution: string;
               notes: string }[];
  never_collected: string[];
}

export interface Downloads {
  generated_at: string | null;
  is_demo: boolean | null;
  licence?: string;
  files: { name: string; rows: number; bytes: number; sha256: string; description: string;
           url: string }[];
}

export interface Status {
  data_mode: DataMode;
  coverage_pct: number | null;
  fares_last_30_days: number;
  exclusions: { reason: string; description: string; fares: number }[];
  recent_errors: { route: string; error: string; at: string | null }[];
  providers: Record<string, {
    display_name: string;
    kind: string | null;
    last_run: { date: string; status: string; routes_ok: number; routes_requested: number;
                calls: number; message: string | null } | null;
    route_success_pct: number | null;
    terms_reviewed: boolean;
    days: { date: string; status: string }[];
  }>;
}
