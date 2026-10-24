import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { getMethodology } from "@/lib/api";
import { dayMonthYear, inr, routeSlug } from "@/lib/format";
import { REPO_URL } from "@/lib/site";

import styles from "./methodology.module.css";

export const metadata: Metadata = {
  title: "Methodology",
  description: "How AeroPulse turns cheapest fares into an index: collection, cleaning, the Jevons chain-linked index, uncertainty and the “usual” verdict.",
};

async function Body() {
  const m = await getMethodology();
  const steps = [
    { title: "Collect", text: <>Every day, for each route, a licensed fare API returns the cheapest economy one-way fare for each
        departure date in the next 60 days. Nothing is scraped and nothing about travellers is stored.</> },
    { title: "Clean", text: <>Fares must be in rupees and between {inr(m.price_floor_inr)} and {inr(m.price_ceiling_inr)}. A fare more
        than {m.outlier_z} robust standard deviations from the others on the same route, window and day is set aside.
        Every exclusion is counted and published.</> },
    { title: "Summarise", text: <>Departure dates are grouped into {m.windows.length} booking windows. For each route, window and day we
        take the median of the cheapest fares. A day needs at least {m.min_dates_per_product_day} departure dates to count.</> },
    { title: "Index", text: <>Day-to-day changes are combined with a Jevons index (a geometric mean of price ratios), weighted by route,
        and chained so the basket can change without breaking the series. The first {m.base_days} days set the base of 100.</> },
    { title: "Measure uncertainty", text: <>We resample departure dates {m.se_replications} times (seed {m.se_seed}) and recompute. The
        middle 95% of those results is the ribbon&apos;s thickness.</> },
    { title: "Give a verdict", text: <>Today&apos;s fare is compared with the {m.typical_low_pct}th to {m.typical_high_pct}th percentile of the
        last {m.typical_lookback_days} days. With fewer than {m.min_history_for_verdict} days of history, no verdict is given.</> },
  ];
  const weights = m.weights.filter((w) => w.basket_version === m.weights[0]?.basket_version)
    .sort((a, b) => b.weight - a.weight);
  const totalWeight = weights.reduce((s, w) => s + w.weight, 0) || 1;
  const maxWeight = Math.max(...weights.map((w) => w.weight), 0.0001);
  const equal = weights.every((w) => Math.abs(w.weight - weights[0].weight) < 1e-9);

  return (
    <>
      <section aria-labelledby="h-steps">
        <SectionHead id="h-steps" icon="route" title="From fare to index, in six steps" />
        <ol className={styles.steps}>
          {steps.map((s, i) => (
            <li key={s.title} className="card">
              <span className={styles.num} aria-hidden="true">{i + 1}</span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="section" aria-labelledby="h-formula">
        <SectionHead id="h-formula" icon="index" title="The formula" />
        <div className={`card ${styles.formula}`}>
          <p className={styles.eq}>
            I<sub>t</sub> = I<sub>t−1</sub> × ∏<sub>r</sub> (p<sub>r,t</sub> / p<sub>r,t−1</sub>)<sup>w<sub>r</sub></sup>
          </p>
          <p className="muted">
            I is the index, p<sub>r,t</sub> the median cheapest fare on route r on day t, and w<sub>r</sub> the route&apos;s weight
            (weights add up to 1). Routes missing on either day drop out of that day&apos;s link and the remaining weights are
            rescaled. A day is published only when at least {m.coverage_publish_pct}% of the basket weight is present;
            below {m.coverage_warn_pct}% we flag it.
          </p>
        </div>
      </section>

      <section className="section" aria-labelledby="h-weights">
        <SectionHead id="h-weights" icon="compare" title="Route weights"
                     aside={weights[0] ? `Basket ${weights[0].basket_version}` : undefined} />
        <div className="card">
          {equal ? (
            <>
              <p className={styles.equal}>
                All {weights.length} routes count the same: {(100 / weights.length).toFixed(1)}% each. Weights based on
                passenger numbers will replace these once enough traffic data is linked.
              </p>
              <ul className={styles.routeList}>
                {weights.map((w) => (
                  <li key={w.route}><Link href={`/routes/${routeSlug(w.route)}`}>{w.route.replace("-", " → ")}</Link></li>
                ))}
              </ul>
            </>
          ) : (
          <ul className={styles.weights}>
            {weights.map((w) => (
              <li key={w.route}>
                <Link href={`/routes/${routeSlug(w.route)}`} className={styles.wRoute}>{w.route.replace("-", " → ")}</Link>
                <span className={styles.bar}><span style={{ width: `${(w.weight / maxWeight) * 100}%` }} /></span>
                <span className={styles.wVal}>{((w.weight / totalWeight) * 100).toFixed(1)}%</span>
              </li>
            ))}
          </ul>
          )}
          {weights[0] && !equal && <p className="small muted mt-3">Source of weights: {weights[0].source}.</p>}
        </div>
      </section>

      <section className="section" aria-labelledby="h-excl">
        <SectionHead id="h-excl" icon="shield" title="Why a fare can be set aside" />
        <dl className={styles.reasons}>
          {Object.entries(m.exclusion_reasons).map(([k, v]) => (
            <div key={k} className="card"><dt><code>{k}</code></dt><dd>{v}</dd></div>
          ))}
        </dl>
        <p className="small muted mt-3">Counts for the last 30 days are on the <Link href="/status">status page</Link>.</p>
      </section>

      {m.links.length > 0 && (
        <section className="section" aria-labelledby="h-links">
          <SectionHead id="h-links" icon="data" title="Chain links" />
          <div className="card table-scroll">
            <table className="table">
              <thead><tr><th>Series</th><th>From</th><th>To</th><th>Linked on</th><th>Factor</th></tr></thead>
              <tbody>
                {m.links.map((l) => (
                  <tr key={`${l.series}-${l.link_date}`}>
                    <td>{l.series}</td><td>{l.from_version}</td><td>{l.to_version}</td>
                    <td>{dayMonthYear(l.link_date)}</td><td>{l.factor.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="section" aria-labelledby="h-more">
        <SectionHead id="h-more" icon="book" title="Read the full method" />
        <p className={styles.more}>
          This page is the short version of methodology {m.version}. The long version, with every decision and the
          reasoning behind it, is in the <a href={`${REPO_URL}/tree/main/docs/methodology`}>methodology documents</a>, and
          the code that does the work is open in the <a href={REPO_URL}>repository</a>.
        </p>
      </section>
    </>
  );
}

export default function MethodologyPage() {
  return (
    <>
      <PageHead icon="index" title="How the index is made"
                lede="Every number on AeroPulse comes from the same six steps. Here they are, with the actual settings." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Loading the method…</p>}><Body /></Suspense>
      </div>
    </>
  );
}
