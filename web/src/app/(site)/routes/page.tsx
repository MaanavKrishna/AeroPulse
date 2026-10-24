import type { Metadata } from "next";
import { Suspense } from "react";

import { RouteMap } from "@/components/charts/RouteMap";
import { RouteExplorer } from "@/components/routes/RouteExplorer";
import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { getAirports, getRoutes } from "@/lib/api";

export const metadata: Metadata = {
  title: "All routes: Indian domestic fares against usual",
  description: "Every route AeroPulse tracks, with today's verdict and the last 90 days.",
};

async function Explorer() {
  const [routes, airports] = await Promise.all([getRoutes(), getAirports()]);
  return (
    <>
      <RouteExplorer routes={routes} airports={airports} />
      <section className="section" aria-labelledby="h-chart">
        <SectionHead id="h-chart" icon="pin" title="On the chart" aside="Every lane is a link" />
        <RouteMap airports={airports} routes={routes} />
      </section>
    </>
  );
}

export default function RoutesPage() {
  return (
    <>
      <PageHead icon="route" title="Every route we track"
                lede="40 routes between 13 of India's busiest airports, both directions. Each line shows the last 90 days against that route's own usual range." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Loading routes…</p>}>
          <Explorer />
        </Suspense>
      </div>
    </>
  );
}
