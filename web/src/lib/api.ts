// Server-side data access. Every page reads the AeroPulse API through these functions.
// Results are cached for an hour: fares are collected every few hours, so pages stay fresh
// without hitting the API on every visit.
import { cacheLife } from "next/cache";

import type {
  AirportDetail, Airport, Downloads, Festival, FestivalDetail, Insights, Meta, Methodology,
  RouteCalendar, RouteDetail, RouteFares, RouteRow, Sources, Status,
} from "./types";

import { API_URL } from "./api-url";

export { API_URL };

// Server-only settings. Never NEXT_PUBLIC_.
// A private address for the API when the server can reach it directly (e.g. inside Docker).
const SERVER_API_URL = (process.env.AEROPULSE_API_INTERNAL_URL ?? API_URL).replace(/\/$/, "");
// A shared secret that lets this site skip the API's per-IP rate limit.
const SITE_KEY = process.env.AEROPULSE_SITE_KEY;

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function fetchJson<T>(path: string): Promise<T | null> {
  "use cache";
  cacheLife("hours");
  const headers: Record<string, string> = { Accept: "application/json" };
  if (SITE_KEY) headers["X-AeroPulse-Site-Key"] = SITE_KEY;
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(`${SERVER_API_URL}${path}`, { headers });
    if (res.status === 404) return null;
    // Rate limited: wait as long as the API asks (capped) and try again, a few times.
    if (res.status === 429 && attempt < 4) {
      const after = Number(res.headers.get("Retry-After")) || 5;
      await wait(Math.min(after, 30) * 1000);
      continue;
    }
    if (!res.ok) throw new Error(`AeroPulse API ${res.status} for ${path}`);
    return (await res.json()) as T;
  }
}

async function must<T>(path: string): Promise<T> {
  const data = await fetchJson<T>(path);
  if (data === null) throw new Error(`AeroPulse API returned nothing for ${path}`);
  return data;
}

export const getMeta = () => must<Meta>("/v1/meta");
export const getInsights = () => must<Insights>("/v1/insights");
export const getRoutes = async () => (await must<{ routes: RouteRow[] }>("/v1/routes")).routes;
export const getRoute = (id: string) => fetchJson<RouteDetail>(`/v1/routes/${id.toUpperCase()}`);
export const getRouteFares = (id: string, window: string, days: number | null = 90) =>
  fetchJson<RouteFares>(
    `/v1/routes/${id.toUpperCase()}/fares?window=${window}${days ? `&days=${days}` : ""}`);
export const getCalendar = (id: string) =>
  fetchJson<RouteCalendar>(`/v1/routes/${id.toUpperCase()}/calendar`);
export const getAirports = async () =>
  (await must<{ airports: Airport[] }>("/v1/airports")).airports;
export const getAirport = (iata: string) =>
  fetchJson<AirportDetail>(`/v1/airports/${iata.toUpperCase()}`);
export const getFestivals = async () =>
  (await must<{ festivals: Festival[] }>("/v1/festivals")).festivals;
export const getFestival = (slug: string) => fetchJson<FestivalDetail>(`/v1/festivals/${slug}`);
export const getMethodology = () => must<Methodology>("/v1/methodology");
export const getSources = () => must<Sources>("/v1/sources");
export const getDownloads = () => must<Downloads>("/v1/downloads");
export const getStatus = () => must<Status>("/v1/status");

/** Absolute URL for files the API serves (CSV, images, feeds, dataset). */
export const apiFile = (path: string) => `${API_URL}${path}`;
