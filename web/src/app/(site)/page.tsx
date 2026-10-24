import Link from "next/link";
import { Suspense } from "react";

import { BookingCurve } from "@/components/charts/BookingCurve";
import { FareRibbon } from "@/components/charts/FareRibbon";
import { WeekdayBars } from "@/components/charts/WeekdayBars";
import { HeroExplorer } from "@/components/home/HeroExplorer";
import { Movers } from "@/components/home/Movers";
import { FestivalBoard } from "@/components/ui/FestivalBoard";
import { RouteRows } from "@/components/ui/RouteRows";
import { Pictogram } from "@/components/ui/Pictogram";
import { SectionHead } from "@/components/ui/SectionHead";
import { Mark } from "@/components/ui/Verdict";
import { getAirports, getFestivals, getInsights, getMeta, getRouteFares, getRoutes } from "@/lib/api";
import { cheapestSentence, indexVerdict } from "@/lib/copy";
import { dayMonthYear, signedPct } from "@/lib/format";
import { cheapestStretch, lastMinutePremium, nationalCurve, weekdaySentence } from "@/lib/insight";
import { DEFAULT_ROUTE, DEFAULT_WINDOW } from "@/lib/site";

import styles from "./home.module.css";

async function Hero() {
  const [meta, routes, airports, fares] = await Promise.all([
    getMeta(), getRoutes(), getAirports(), getRouteFares(DEFAULT_ROUTE, DEFAULT_WINDOW),
  ]);
  const asOf = meta.latest_date
    ? `Fares as of ${dayMonthYear(meta.latest_date)}${meta.data_mode === "demo" ? ", demo data" : ""}` : "";
  return (
    <HeroExplorer routes={routes} airports={airports} windows={meta.windows} asOf={asOf}
                  initialRoute={DEFAULT_ROUTE} initialWindow={DEFAULT_WINDOW} initialFares={fares!} />
  );
}

async function National() {
  const i = await getInsights();
  const n = i.national;
  const curve = nationalCurve(i);
  const stretch = cheapestStretch(curve);
  const premium = lastMinutePremium(i);
  return (
    <>
      <section className="section" aria-labelledby="h-week">
        <SectionHead id="h-week" icon="week" title="This week" aside={`Routes that moved most in the last ${i.movers.lag_days} days`} />
        <div className="card"><Movers up={i.movers.up} down={i.movers.down} /></div>
      </section>

      <section className="section" aria-labelledby="h-national">
        <div className={`card ${styles.national}`}>
          <div>
            <h2 id="h-national" className={styles.kicker}><span className="sign-tile"><Pictogram name="index" /></span>Across India</h2>
            <p className={styles.statement}><Mark v={n.verdict} />{indexVerdict(n.verdict)}</p>
            <dl className="strip">
              <div><dt>National index</dt><dd>{n.series.at(-1)?.[1].toFixed(1)}</dd></div>
              <div><dt>Last 30 days</dt><dd>{signedPct(n.change_30d_pct)}</dd></div>
              <div><dt>History</dt><dd>{n.history_days} days</dd></div>
            </dl>
            <p className="small muted mt-3">
              {n.early_series && "Early series: less than 90 days of data so far. "}
              100 is the average of the first week of collection. <Link href="/trends">See all trends</Link>
            </p>
          </div>
          <FareRibbon points={n.series} typical={n.verdict} unit="index" size="lg"
                      label={`National airfare index, last 90 days. ${indexVerdict(n.verdict)}`} />
        </div>
      </section>

      <section className="section" aria-labelledby="h-when">
        <SectionHead id="h-when" icon="clock" title="When to book, and which day to fly" aside="All routes, last 30 days" />
        <div className="split">
          <div className="card">
            <p className={styles.finding}>{cheapestSentence(stretch).replace("Over the last month, fares", "Across all routes, fares")}</p>
            {premium != null && <p className="muted mt-3">Booking in the last three days cost {premium.toFixed(0)}% more than usual for the route.</p>}
            <div className="mt-5">
              <BookingCurve points={curve} cheap={stretch} unit="pct"
                            label="Cheapest fare by days before departure, as % against each route's usual, all routes" />
            </div>
          </div>
          <div className="card">
            <p className={styles.finding}>{weekdaySentence(i.weekdays)}</p>
            <p className="muted mt-3">Compared at the same booking distance, 8 to 45 days out.</p>
            <div className="mt-5"><WeekdayBars data={i.weekdays} label="Cheapest fare by day of departure, all routes" /></div>
          </div>
        </div>
      </section>
    </>
  );
}

async function FurthestFromUsual() {
  const rows = (await getRoutes()).sort((a, b) => (b.verdict.pct_vs_usual ?? 0) - (a.verdict.pct_vs_usual ?? 0));
  return (
    <section className="section" aria-labelledby="h-routes">
      <SectionHead id="h-routes" icon="route" title="Routes furthest from usual" aside={<Link href="/routes">All {rows.length} routes</Link>} />
      <RouteRows rows={rows.slice(0, 6)} />
    </section>
  );
}

async function Festivals() {
  const all = await getFestivals();
  const today = (await getMeta()).latest_date ?? all[0]?.date;
  const upcoming = all.filter((f) => f.date >= (today ?? "")).slice(0, 3);
  if (!upcoming.length) return null;
  return (
    <section className="section" aria-labelledby="h-fest">
      <SectionHead id="h-fest" icon="lamp" title="Festival travel" aside="The busiest travel day, against ordinary weeks" />
      <FestivalBoard festivals={upcoming} today={today!} />
    </section>
  );
}

export default function Home() {
  return (
    <>
    <div className={`sign sign-band ${styles.heroBand}`}>
      <div className="wrap">
        <Suspense fallback={<div className={styles.heroSkeleton} aria-hidden="true" />}>
          <Hero />
        </Suspense>
      </div>
    </div>
    <div className="wrap">
      <Suspense fallback={null}><National /></Suspense>
      <Suspense fallback={null}><FurthestFromUsual /></Suspense>
      <Suspense fallback={null}><Festivals /></Suspense>
      <section className="section" aria-labelledby="h-new">
        <SectionHead id="h-new" icon="info" title="New here?" aside={<Link href="/guide">Read the two-minute guide</Link>} />
        <ol className={styles.steps}>
          <li><h3>Pick a route</h3><p>40 routes between India&apos;s busiest airports, both directions.</p></li>
          <li><h3>Pick when you&apos;re flying</h3><p>Fares behave differently a week out and two months out, so each is judged separately.</p></li>
          <li><h3>Read the answer</h3><p>We compare today&apos;s cheapest fares with the middle half of the last 90 days. That band is &ldquo;usual&rdquo;.</p></li>
        </ol>
      </section>
    </div>
    </>
  );
}
