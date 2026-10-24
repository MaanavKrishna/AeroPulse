import type { MetadataRoute } from "next";

import { getAirports, getFestivals, getRoutes } from "@/lib/api";
import { routeSlug } from "@/lib/format";
import { NAV, SITE_URL } from "@/lib/site";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [routes, airports, festivals] = await Promise.all([getRoutes(), getAirports(), getFestivals()]);
  const pages = ["", ...NAV.map((n) => n.href), "/methodology", "/status", "/about"];
  return [
    ...pages.map((p) => ({ url: `${SITE_URL}${p}` })),
    ...routes.map((r) => ({ url: `${SITE_URL}/routes/${routeSlug(r.route)}` })),
    ...airports.map((a) => ({ url: `${SITE_URL}/airports/${a.iata}` })),
    ...festivals.map((f) => ({ url: `${SITE_URL}/festivals/${f.slug}` })),
  ];
}
