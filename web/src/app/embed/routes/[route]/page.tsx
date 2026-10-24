import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { FareRibbon } from "@/components/charts/FareRibbon";
import { VerdictChip } from "@/components/ui/Verdict";
import { getRoute, getRouteFares, getRoutes } from "@/lib/api";
import { answer } from "@/lib/copy";
import { rupees, routeSlug } from "@/lib/format";
import { DEFAULT_WINDOW, SITE_URL } from "@/lib/site";

import styles from "./embed.module.css";

export const metadata: Metadata = { robots: { index: false } };

export async function generateStaticParams() {
  const routes = await getRoutes();
  return routes.map((r) => ({ route: routeSlug(r.route) }));
}

async function Embed({ params }: { params: PageProps<"/embed/routes/[route]">["params"] }) {
  const { route } = await params;
  const [d, fares] = await Promise.all([getRoute(route), getRouteFares(route, DEFAULT_WINDOW)]);
  if (!d || !fares) notFound();
  const w = d.windows.find((x) => x.window === DEFAULT_WINDOW);
  return (
    <main className={styles.embed}>
      <header className={styles.head}>
        <div>
          <p className={styles.name}>{d.origin.city} to {d.destination.city}</p>
          <p className={styles.sub}>Cheapest fare, booking {w?.label ?? "2–4 weeks out"}</p>
        </div>
        <div className={styles.now}>
          {fares.latest && <span className={styles.price}>{rupees(fares.latest.median_inr)}</span>}
          <VerdictChip v={fares.verdict} />
        </div>
      </header>
      <FareRibbon points={fares.points} typical={fares.verdict} size="md" label={answer(fares.verdict)} />
      <footer className={styles.foot}>
        <a href={`${SITE_URL}/routes/${routeSlug(d.route)}`} target="_blank" rel="noopener">AeroPulse</a>
        {fares.data_mode === "demo" ? <strong>Demo data, not real fares</strong> : <span>CC BY 4.0</span>}
      </footer>
    </main>
  );
}

export default function EmbedPage({ params }: PageProps<"/embed/routes/[route]">) {
  return <Suspense fallback={null}><Embed params={params} /></Suspense>;
}
