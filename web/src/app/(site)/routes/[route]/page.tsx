import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense, ViewTransition } from "react";

import { BookingCurve } from "@/components/charts/BookingCurve";
import { FareRibbon } from "@/components/charts/FareRibbon";
import { WeekdayBars } from "@/components/charts/WeekdayBars";
import { DepartureCalendar } from "@/components/routes/DepartureCalendar";
import { RouteFaresPanel } from "@/components/routes/RouteFaresPanel";
import { RouteLeg } from "@/components/routes/RouteLeg";
import { CopyButton } from "@/components/ui/CopyButton";
import { RouteRows } from "@/components/ui/RouteRows";
import { SectionHead } from "@/components/ui/SectionHead";
import { apiFile, getCalendar, getMeta, getRoute, getRouteFares, getRoutes } from "@/lib/api";
import { answer, cheapestSentence, indexVerdict } from "@/lib/copy";
import { dayMonthYear, routeSlug } from "@/lib/format";
import { weekdaySentence } from "@/lib/insight";
import { DEFAULT_WINDOW, SITE_URL } from "@/lib/site";

import styles from "@/components/routes/route.module.css";

export async function generateStaticParams() {
  const routes = await getRoutes();
  return routes.map((r) => ({ route: routeSlug(r.route) }));
}

export async function generateMetadata({ params }: PageProps<"/routes/[route]">): Promise<Metadata> {
  const { route } = await params;
  const d = await getRoute(route);
  if (!d) return { title: "Route not found" };
  const w = d.windows.find((x) => x.window === DEFAULT_WINDOW) ?? d.windows[0];
  return {
    title: `${d.origin.city} to ${d.destination.city} flight fares: today vs usual`,
    description: `${answer(w.verdict)} Cheapest fares, booking-window verdicts, when to book and which day to fly on ${d.name}.`,
    openGraph: { images: [apiFile(`/img/routes/${route}.svg?w=${DEFAULT_WINDOW}`)] },
    alternates: { types: { "application/atom+xml": apiFile(`/feeds/routes/${route}.xml`) } },
  };
}

async function Route({ params }: { params: PageProps<"/routes/[route]">["params"] }) {
  const { route } = await params;
  const [d, fares, cal, meta, all] = await Promise.all([
    getRoute(route), getRouteFares(route, DEFAULT_WINDOW), getCalendar(route), getMeta(), getRoutes(),
  ]);
  if (!d || !fares || !cal) notFound();
  const slug = routeSlug(d.route);
  const from = d.origin.city, to = d.destination.city;
  const related = all.filter((r) => r.route !== d.route && (r.origin === d.origin.iata || r.destination === d.destination.iata));
  const reverse = d.reverse ? all.find((r) => r.route === d.reverse) : null;
  const citation = `AeroPulse, "${from} to ${to}: cheapest fares", ${meta.latest_date ? dayMonthYear(meta.latest_date) : ""}. ${SITE_URL}/routes/${slug}${meta.data_mode === "demo" ? " [DEMO DATA]" : ""}`;
  const embed = `<iframe src="${SITE_URL}/embed/routes/${slug}" title="${from} to ${to} fares, AeroPulse" width="100%" height="320" style="border:0" loading="lazy"></iframe>`;

  return (
    <>
      <RouteFaresPanel detail={d} initial={fares} initialWindow={DEFAULT_WINDOW} header={
        <>
          <p className="crumbs"><Link href="/routes">Routes</Link> / {d.origin.iata} to {d.destination.iata}</p>
          <div className={styles.titlebar}>
            <ViewTransition name={`route-${slug}`}>
              <h1 id="route-title" className={styles.title}>{from} to {to}</h1>
            </ViewTransition>
            {d.reverse && <Link className={styles.pill} href={`/routes/${routeSlug(d.reverse)}`}>Flip to {to} to {from}</Link>}
            <Link className={styles.pill} href={`/compare?routes=${d.route}${d.reverse ? `,${d.reverse}` : ""}`}>Compare</Link>
          </div>
          <RouteLeg origin={d.origin} destination={d.destination} km={d.distance_km} level={fares.verdict.level} />
        </>
      } />
      <div className="wrap">

      <section className="section" aria-labelledby="h-when">
        <div className="split split-wide">
          <div className="card">
            <SectionHead id="h-when" icon="clock" title="When this route is cheapest" aside="Last 30 days" />
            <BookingCurve points={d.booking_curve.map((c) => ({ days_ahead: c.days_ahead, value: c.median_inr }))}
                          cheap={d.usually_cheapest_days_ahead} unit="inr"
                          label={`Median cheapest fare by days before departure, ${from} to ${to}`} />
            <p className="mt-5">{cheapestSentence(d.usually_cheapest_days_ahead)}</p>
            <p className="small muted mt-3">This describes the recent past, not what fares will do.</p>
          </div>
          <div className="card">
            <SectionHead id="h-day" icon="calendar" title="Which day to fly" />
            <WeekdayBars data={d.weekdays} label={`Cheapest fare by day of departure, ${from} to ${to}`} />
            <p className="mt-4">{weekdaySentence(d.weekdays)}</p>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="h-cal">
        <SectionHead id="h-cal" icon="departures" title="Next departures" aside="The next two months, date by date" />
        <DepartureCalendar cal={cal} />
      </section>

      {(reverse || related.length > 0) && (
        <section className="section" aria-labelledby="h-related">
          <SectionHead id="h-related" icon="route" title="Related routes" aside={`The way back, and other routes from ${from} or to ${to}`} />
          <RouteRows rows={[...(reverse ? [reverse] : []), ...related.filter((r) => r.route !== reverse?.route)].slice(0, 6)} />
        </section>
      )}

      <section className="section" aria-labelledby="h-use">
        <SectionHead id="h-use" icon="data" title="Use this data" aside="Free to reuse under CC BY 4.0. Please credit AeroPulse." />
        <div className="split">
          <div className={styles.cite}>
            <pre className="snippet">{citation}</pre>
            <div className="actions">
              <CopyButton text={citation} label="Copy citation" />
              <a className="btn btn-quiet" href={apiFile(`/csv/routes/${slug}.csv?w=${DEFAULT_WINDOW}`)}>Download CSV</a>
              <a className="btn btn-quiet" href={apiFile(`/img/routes/${slug}.svg?w=${DEFAULT_WINDOW}`)}>Chart image</a>
              <a className="btn btn-quiet" href={apiFile(`/feeds/routes/${slug}.xml`)}>Follow by feed</a>
            </div>
          </div>
          <div className={styles.cite}>
            <pre className="snippet">{embed}</pre>
            <div className="actions"><CopyButton text={embed} label="Copy embed code" /></div>
          </div>
        </div>
      </section>

      <section className="section" aria-labelledby="h-index">
        <SectionHead id="h-index" icon="index" title="Route index" aside="All four booking windows combined, 100 at the start of collection" />
        <div className="split split-wide">
          <FareRibbon points={d.index.series} typical={d.index.verdict} unit="index" size="md" label={`Route index, ${from} to ${to}`} />
          <div>
            <p>{indexVerdict(d.index.verdict, "Fares on this route")}</p>
            <p className="small muted mt-3">Every day we ask a licensed fare provider for the cheapest economy one-way fare on each
              departure date over the next two months. For each booking window we take the median of those fares; the index
              combines the four windows equally. <Link href="/methodology">Read the full method</Link></p>
          </div>
        </div>
      </section>
      </div>
    </>
  );
}

export default function RoutePage(props: PageProps<"/routes/[route]">) {
  return (
    <Suspense fallback={<div className="sign sign-band"><div className="wrap page-head"><p className="muted">Loading route…</p></div></div>}>
      <Route params={props.params} />
    </Suspense>
  );
}
