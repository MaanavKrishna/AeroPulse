import type { MetadataRoute } from "next";

import { getMeta } from "@/lib/api";
import { SITE_URL } from "@/lib/site";

// While the site runs on demo data, keep it out of search results so nobody finds fake fares by searching.
export default async function robots(): Promise<MetadataRoute.Robots> {
  const meta = await getMeta();
  if (meta.data_mode !== "live") return { rules: { userAgent: "*", disallow: "/" } };
  return {
    rules: { userAgent: "*", allow: "/", disallow: "/embed/" },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
