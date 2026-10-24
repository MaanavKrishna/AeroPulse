import type { Metadata } from "next";
import { Suspense } from "react";

import { BookingCurve } from "@/components/charts/BookingCurve";
import { FareRibbon } from "@/components/charts/FareRibbon";
import { MultiLine } from "@/components/charts/MultiLine";
import { WeekdayBars } from "@/components/charts/WeekdayBars";
import { Movers } from "@/components/home/Movers";
import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { VerdictChip } from "@/components/ui/Verdict";
import { getInsights } from "@/lib/api";
import { cheapestSentence, indexVerdict } from "@/lib/copy";
import { signedPct } from "@/lib/format";
import { cheapestStretch, lastMinutePremium, nationalCurve, weekdaySentence } from "@/lib/insight";

import styles from "./trends.module.css";

export const metadata: Metadata = {
  title: "Trends: Indian airfares across the country",
  description: "The national airfare index, how each booking window is moving, which routes moved most, when to book and which day to fly.",
};

async function Trends() {
  const i = await getInsights();
  const n = i.national;
  const curve = nationalCurve(i);
  const stretch = cheapestStretch(curve);
  const premium = lastMinutePremium(i);
  return (
    <>
      <PageHead icon="trend" title="Trends across India" lede={indexVerdict(n.verdict)}>
        <dl className="strip">
          <div><dt>National index</dt><dd>{n.series.at(-1)?.[1].toFixed(1)}</dd></div>
          <div><dt>Last 30 days</dt><dd>{signedPct(n.change_30d_pct)}</dd></div>
          <div><dt>Last-minute premium</dt><dd>{premium != null ? `+${premium.toFixed(0)}%` : "–"}</dd></div>
          <div><dt>History</dt><dd>{n.history_days} days</dd></div>
        </dl>
      </PageHead>
      <div className="wrap page-body">
        <section aria-labelledby="h-nat">
          <SectionHead id="h-nat" icon="index" title="National index" aside="All 40 routes, chain-linked, 100 at the start" />
          <div className="card"><FareRibbon points={n.series} typical={n.verdict} unit="index" size="lg"
                                            label={`National airfare index. ${indexVerdict(n.verdict)}`} /></div>
        </section>

        <section className="section" aria-labelledby="h-win">
          <SectionHead id="h-win" icon="clock" title="By how far ahead you book" aside="Each window's index, rebased to 100 at the start of the chart" />
          <div className={styles.windows}>
            <div className="card">
              <MultiLine lines={i.windows.map((w) => ({ id: w.key, label: w.label, points: w.series }))}
                         label="Booking-window indices compared" />
            </div>
            <ul className={styles.windowList}>
              {i.windows.map((w, k) => (
                <li key={w.key} className="card">
                  <span className={styles.swatch} style={{ background: `var(--cat-${k + 1})` }} />
                  <span className={styles.wName}>{w.label.charAt(0).toUpperCase() + w.label.slice(1)}</span>
                  <VerdictChip v={w.verdict} />
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="section" aria-labelledby="h-movers">
          <SectionHead id="h-movers" icon="week" title="Biggest moves this week" aside={`Change in each route's index over ${i.movers.lag_days} days`} />
          <div className="card"><Movers up={i.movers.up} down={i.movers.down} /></div>
        </section>

        <section className="section" aria-labelledby="h-book">
          <div className="split">
            <div className="card">
              <SectionHead id="h-book" icon="clock" title="When to book" />
              <p className={styles.finding}>{cheapestSentence(stretch).replace("Over the last month, fares", "Across all routes, fares")}</p>
              <div className="mt-5"><BookingCurve points={curve} cheap={stretch} unit="pct"
                                                  label="Cheapest fare by days before departure, all routes" /></div>
            </div>
            <div className="card">
              <SectionHead id="h-day" icon="calendar" title="Which day to fly" />
              <p className={styles.finding}>{weekdaySentence(i.weekdays)}</p>
              <div className="mt-5"><WeekdayBars data={i.weekdays} label="Cheapest fare by day of departure, all routes" /></div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

export default function TrendsPage() {
  return <Suspense fallback={<div className="sign sign-band"><div className="wrap page-head"><p>Loading trends…</p></div></div>}><Trends /></Suspense>;
}
