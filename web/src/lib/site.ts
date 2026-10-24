// Site-wide constants.
export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_PROJECT_PRODUCTION_URL ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : "http://localhost:3000")
).replace(/\/$/, "");

export const REPO_URL = "https://github.com/MaanavKrishna/AeroPulse";

export const NAV = [
  { href: "/routes", label: "Routes" },
  { href: "/airports", label: "Airports" },
  { href: "/trends", label: "Trends" },
  { href: "/festivals", label: "Festivals" },
  { href: "/compare", label: "Compare" },
  { href: "/guide", label: "Guide" },
  { href: "/data", label: "Data" },
] as const;

export const DEFAULT_ROUTE = "DEL-BOM";
export const DEFAULT_WINDOW = "15-30";
