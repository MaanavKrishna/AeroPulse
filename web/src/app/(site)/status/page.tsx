import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { getStatus } from "@/lib/api";
import { dayMonth, dayMonthYear } from "@/lib/format";

import styles from "./status.module.css";

export const metadata: Metadata = {
  title: "Collection status",
  description: "Is AeroPulse collecting fares? Daily runs, coverage, exclusions and recent errors.",
};

const STATUS_LABEL: Record<string, string> = { ok: "Complete", partial: "Partial", failed: "Failed", skipped: "Skipped" };

async function Body() {
  const s = await getStatus();
  const providers = Object.entries(s.providers);
  const healthy = providers.length > 0 && providers.every(([, p]) => p.last_run?.status === "ok");
  const totalExcluded = s.exclusions.reduce((n, e) => n + e.fares, 0);
  return (
    <>
      <div className={`${styles.banner} ${healthy ? styles.ok : styles.warn}`} role="status">
        <span className={styles.light} aria-hidden="true" />
        <div>
          <p className={styles.bannerTitle}>{healthy ? "Collection is running normally" : "Collection needs attention"}</p>
          <p className={styles.bannerSub}>
            {s.data_mode === "demo" ? "Running on the demo generator, not real fares." :
              s.data_mode === "empty" ? "No fares collected yet." : "Collecting real fares from licensed sources."}
          </p>
        </div>
      </div>

      <dl className="strip">
        <div><dt>Basket coverage today</dt><dd>{s.coverage_pct == null ? "–" : `${Math.round(s.coverage_pct)}%`}</dd></div>
        <div><dt>Fares in the last 30 days</dt><dd>{s.fares_last_30_days.toLocaleString("en-IN")}</dd></div>
        <div><dt>Set aside</dt><dd>{totalExcluded.toLocaleString("en-IN")}</dd></div>
        <div><dt>Recent errors</dt><dd>{s.recent_errors.length}</dd></div>
      </dl>

      <section className="section" aria-labelledby="h-runs">
        <SectionHead id="h-runs" icon="calendar" title="Daily runs" aside="Last 30 days" />
        <div className={styles.providers}>
          {providers.map(([key, p]) => (
            <article key={key} className="card">
              <header className={styles.pHead}>
                <h3>{p.display_name}</h3>
                {p.kind && <span className="chip">{p.kind}</span>}
              </header>
              <ol className={styles.days} aria-label={`Daily runs for ${p.display_name}`}>
                {p.days.map((d) => (
                  <li key={d.date} className={styles[`d_${d.status}`] ?? styles.d_none}
                      title={`${dayMonth(d.date)}: ${STATUS_LABEL[d.status] ?? d.status}`}>
                    <span className="visually-hidden">{dayMonth(d.date)}: {STATUS_LABEL[d.status] ?? d.status}</span>
                  </li>
                ))}
              </ol>
              {p.last_run ? (
                <p className="small muted mt-3">
                  Last run {dayMonthYear(p.last_run.date)}: {p.last_run.routes_ok} of {p.last_run.routes_requested} routes,
                  {" "}{p.last_run.calls} API calls{p.route_success_pct != null && <>, {Math.round(p.route_success_pct)}% success over 30 days</>}.
                  {p.last_run.message && <> {p.last_run.message}</>}
                </p>
              ) : <p className="small muted mt-3">No runs yet.</p>}
              {!p.terms_reviewed && <p className="small mt-2"><strong>Terms not yet reviewed.</strong> This source is not used for published numbers.</p>}
            </article>
          ))}
        </div>
        <ul className="legend mt-3">
          <li><span className={`${styles.key} ${styles.d_ok}`} />Complete</li>
          <li><span className={`${styles.key} ${styles.d_partial}`} />Partial</li>
          <li><span className={`${styles.key} ${styles.d_failed}`} />Failed</li>
        </ul>
      </section>

      <section className="section" aria-labelledby="h-excl">
        <SectionHead id="h-excl" icon="shield" title="Fares set aside" aside="Last 30 days" />
        {s.exclusions.length ? (
          <div className="card table-scroll">
            <table className="table">
              <thead><tr><th>Reason</th><th>Fares</th></tr></thead>
              <tbody>
                {s.exclusions.map((e) => (
                  <tr key={e.reason}><td className="wrap">{e.description}</td><td>{e.fares.toLocaleString("en-IN")}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="muted">Nothing set aside.</p>}
        <p className="small muted mt-3">Why fares are set aside is explained in the <Link href="/methodology">methodology</Link>.</p>
      </section>

      <section className="section" aria-labelledby="h-err">
        <SectionHead id="h-err" icon="info" title="Recent errors" />
        {s.recent_errors.length ? (
          <ul className={styles.errors}>
            {s.recent_errors.map((e, i) => (
              <li key={i} className="card"><strong>{e.route}</strong>{e.at && <span className="muted"> · {dayMonthYear(e.at.slice(0, 10))}</span>}<p className="small mt-2">{e.error}</p></li>
            ))}
          </ul>
        ) : <p className="muted">No errors in recent runs.</p>}
      </section>
    </>
  );
}

export default function StatusPage() {
  return (
    <>
      <PageHead icon="check" title="Collection status"
                lede="Whether today's fares arrived, how complete they are, and what was set aside." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Checking…</p>}><Body /></Suspense>
      </div>
    </>
  );
}
