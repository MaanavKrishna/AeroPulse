import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { RouteMap } from "@/components/charts/RouteMap";
import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { getAirports, getRoutes } from "@/lib/api";

import styles from "./airports.module.css";

export const metadata: Metadata = {
  title: "Airports",
  description: "The 13 airports AeroPulse follows, and how fares look on routes from and to each.",
};

async function Airports() {
  const [airports, routes] = await Promise.all([getAirports(), getRoutes()]);
  return (
    <>
      <ul className={styles.grid}>
        {airports.map((a) => {
          const mine = routes.filter((r) => r.origin === a.iata || r.destination === a.iata);
          const up = mine.filter((r) => r.verdict.level === "above").length;
          const down = mine.filter((r) => r.verdict.level === "below").length;
          return (
            <li key={a.iata}>
              <Link href={`/airports/${a.iata.toLowerCase()}`} className={styles.card}>
                <span className={styles.code}>{a.iata}</span>
                <span className={styles.city}>{a.city}</span>
                <span className={styles.name}>{a.airport}, {a.icao}</span>
                <span className={styles.counts}>
                  <span>{mine.length} routes</span>
                  {up > 0 && <span className="chip lv-up">▲ {up} dearer</span>}
                  {down > 0 && <span className="chip lv-down">▼ {down} cheaper</span>}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
      <section className="section" aria-labelledby="h-chart">
        <SectionHead id="h-chart" icon="pin" title="All airports on the chart" />
        <RouteMap airports={airports} routes={routes} />
      </section>
    </>
  );
}

export default function AirportsPage() {
  return (
    <>
      <PageHead icon="pin" title="Airports"
                lede="Thirteen of India's busiest airports. Pick one to see every route we follow from it and to it." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Loading airports…</p>}><Airports /></Suspense>
      </div>
    </>
  );
}
