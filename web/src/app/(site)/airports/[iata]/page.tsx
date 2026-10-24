import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { RouteMap } from "@/components/charts/RouteMap";
import { PageHead } from "@/components/ui/PageHead";
import { RouteRows } from "@/components/ui/RouteRows";
import { SectionHead } from "@/components/ui/SectionHead";
import { getAirport, getAirports, getRoutes } from "@/lib/api";

import styles from "../airports.module.css";

export async function generateStaticParams() {
  const airports = await getAirports();
  return airports.map((a) => ({ iata: a.iata.toLowerCase() }));
}

export async function generateMetadata({ params }: PageProps<"/airports/[iata]">): Promise<Metadata> {
  const { iata } = await params;
  const d = await getAirport(iata);
  return d ? {
    title: `${d.airport.city} (${d.airport.iata}) flight fares`,
    description: `Every route AeroPulse follows from and to ${d.airport.city}, with today's verdict against usual.`,
  } : { title: "Airport not found" };
}

async function Airport({ params }: { params: PageProps<"/airports/[iata]">["params"] }) {
  const { iata } = await params;
  const [d, airports, routes] = await Promise.all([getAirport(iata), getAirports(), getRoutes()]);
  if (!d) notFound();
  const a = d.airport;
  const all = [...d.departures, ...d.arrivals];
  const above = all.filter((r) => r.verdict.level === "above").length;
  const below = all.filter((r) => r.verdict.level === "below").length;
  const furthest = [...all].sort((x, y) => Math.abs(y.verdict.pct_vs_usual ?? 0) - Math.abs(x.verdict.pct_vs_usual ?? 0))[0];

  return (
    <>
      <PageHead icon="pin" crumbs={<><Link href="/airports">Airports</Link> / {a.iata}</>}
                title={<>{a.city} <span style={{ color: "var(--yellow)" }}>{a.iata}</span></>}
                lede={`${a.airport}, ${a.state}. ICAO ${a.icao}.`}>
        <dl className={`strip ${styles.facts}`}>
          <div><dt>Routes followed</dt><dd>{all.length}</dd></div>
          <div><dt>Dearer than usual</dt><dd className="tone-up">{above}</dd></div>
          <div><dt>Cheaper than usual</dt><dd className="tone-down">{below}</dd></div>
          {furthest && <div><dt>Furthest from usual</dt><dd>{furthest.origin}–{furthest.destination}</dd></div>}
        </dl>
      </PageHead>
      <div className="wrap page-body">
        <div className={styles.columns}>
          <section aria-labelledby="h-dep">
            <SectionHead id="h-dep" icon="departures" title={`Departures from ${a.city}`} />
            <RouteRows rows={d.departures} showDistance />
          </section>
          <section aria-labelledby="h-arr">
            <SectionHead id="h-arr" icon="arrivals" title={`Arrivals into ${a.city}`} />
            <RouteRows rows={d.arrivals} showDistance />
          </section>
        </div>
        <section className="section" aria-labelledby="h-chart">
          <SectionHead id="h-chart" icon="route" title={`${a.city} on the chart`} aside="Routes touching this airport are highlighted" />
          <RouteMap airports={airports} routes={routes} focus={a.iata} />
        </section>
      </div>
    </>
  );
}

export default function AirportPage(props: PageProps<"/airports/[iata]">) {
  return (
    <Suspense fallback={<div className="sign sign-band"><div className="wrap page-head"><p>Loading airport…</p></div></div>}>
      <Airport params={props.params} />
    </Suspense>
  );
}
