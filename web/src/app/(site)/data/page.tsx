import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { CopyButton } from "@/components/ui/CopyButton";
import { PageHead } from "@/components/ui/PageHead";
import { Pictogram } from "@/components/ui/Pictogram";
import { SectionHead } from "@/components/ui/SectionHead";
import { apiFile, getDownloads } from "@/lib/api";
import { dayMonthYear, routeSlug } from "@/lib/format";
import { DEFAULT_ROUTE, REPO_URL, SITE_URL } from "@/lib/site";

import styles from "./data.module.css";

export const metadata: Metadata = {
  title: "Open data and API",
  description: "Download every AeroPulse index value and fare summary as CSV, or query the free JSON API. CC BY 4.0.",
};

const ENDPOINTS: [string, string][] = [
  ["/v1/meta", "Data mode, routes, booking windows and the latest date"],
  ["/v1/routes", "Every route with today's verdict and a 90-day series"],
  ["/v1/routes/{id}", "One route: all windows, booking curve, weekday effect"],
  ["/v1/routes/{id}/fares?window=15-30", "Daily fares for one booking window"],
  ["/v1/routes/{id}/calendar", "Cheapest fare for each upcoming departure date"],
  ["/v1/indices/national", "The national index with 95% ranges"],
  ["/v1/airports/{iata}", "Every route from one airport"],
  ["/v1/festivals", "Festival travel windows and how fares behaved"],
  ["/v1/status", "Collection health and exclusions"],
];

function bytes(n: number) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)} MB`;
  if (n >= 1e3) return `${Math.round(n / 1e3)} KB`;
  return `${n} B`;
}

async function Files() {
  const d = await getDownloads();
  if (!d.files.length) {
    return <div className="empty"><h2>No files yet</h2><p>Files appear here after the first daily build.</p></div>;
  }
  return (
    <>
      <ul className={styles.files}>
        {d.files.map((f) => (
          <li key={f.name} className="card">
            <div className={styles.fileTop}>
              <Pictogram name="data" size={26} />
              <a href={apiFile(f.url)} className={styles.fileName} download>{f.name}</a>
            </div>
            <p className={styles.fileDesc}>{f.description}</p>
            <p className={styles.fileMeta}>
              <span>{f.rows.toLocaleString("en-IN")} rows</span><span>{bytes(f.bytes)}</span>
            </p>
            <details className={styles.hash}>
              <summary>SHA-256</summary>
              <code>{f.sha256}</code>
            </details>
          </li>
        ))}
      </ul>
      <p className="small muted mt-4">
        {d.generated_at && <>Built {dayMonthYear(d.generated_at.slice(0, 10))}. </>}
        {d.is_demo && <strong>These files contain demo data, not real fares. </strong>}
        Licence: {d.licence ?? "CC BY 4.0"}.
      </p>
    </>
  );
}

export default function DataPage() {
  const slug = routeSlug(DEFAULT_ROUTE);
  const curl = `curl ${apiFile(`/v1/routes/${DEFAULT_ROUTE}/fares?window=15-30`)}`;
  const embed = `<iframe src="${SITE_URL}/embed/routes/${slug}" width="100%" height="360" style="border:0" title="AeroPulse: Delhi to Mumbai fares"></iframe>`;
  const citation = `AeroPulse: open Indian airfare index. ${SITE_URL}. Licensed CC BY 4.0.`;
  return (
    <>
      <PageHead icon="data" title="Open data"
                lede="Everything behind the charts is free to download and reuse. Credit AeroPulse with a link and you're set." />
      <div className="wrap page-body">
        <section aria-labelledby="h-files">
          <SectionHead id="h-files" icon="data" title="Download the dataset" aside="CSV, updated daily" />
          <Suspense fallback={<p className="muted">Loading files…</p>}><Files /></Suspense>
        </section>

        <section className="section" id="api" aria-labelledby="h-api">
          <SectionHead id="h-api" icon="route" title="JSON API" aside="No key, no sign-up" />
          <div className={styles.apiGrid}>
            <div className="card">
              <p>Try it from a terminal:</p>
              <pre className="snippet mt-3"><code>{curl}</code></pre>
              <div className="mt-3"><CopyButton text={curl} label="Copy command" /></div>
              <p className="small muted mt-4">
                Responses are JSON, cached for an hour and open to any origin (CORS). Please keep it under a few requests a
                second. Full reference: <a href={apiFile("/v1/docs")}>interactive API docs</a>.
              </p>
            </div>
            <div className="card table-scroll">
              <table className="table">
                <thead><tr><th>Endpoint</th><th style={{ textAlign: "left" }}>What it returns</th></tr></thead>
                <tbody>
                  {ENDPOINTS.map(([e, d]) => (
                    <tr key={e}><td><code>{e}</code></td><td className="wrap">{d}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section className="section" aria-labelledby="h-per">
          <SectionHead id="h-per" icon="pin" title="Per-route files" />
          <ul className={styles.perRoute}>
            {[
              ["CSV", `/csv/routes/${slug}.csv`, "Daily fares for every booking window"],
              ["Chart image", `/img/routes/${slug}.svg`, "An SVG of the fare ribbon, ready for an article"],
              ["Feed", `/feeds/routes/${slug}.xml`, "An Atom feed that updates when the verdict changes"],
            ].map(([t, p, d]) => (
              <li key={t} className="card">
                <h3>{t}</h3><p className="muted">{d}</p>
                <a href={apiFile(p)} className="small">{p}</a>
              </li>
            ))}
          </ul>
          <p className="small muted mt-3">Swap <code>{slug}</code> for any route code. Each <Link href="/routes">route page</Link> links its own.</p>
        </section>

        <section className="section" aria-labelledby="h-embed">
          <SectionHead id="h-embed" icon="index" title="Embed and cite" />
          <div className={styles.apiGrid}>
            <div className="card">
              <h3>Embed a live chart</h3>
              <pre className="snippet mt-3"><code>{embed}</code></pre>
              <div className="mt-3"><CopyButton text={embed} label="Copy embed code" /></div>
            </div>
            <div className="card">
              <h3>Cite AeroPulse</h3>
              <p className={`mt-3 ${styles.cite}`}>{citation}</p>
              <div className="mt-3"><CopyButton text={citation} label="Copy citation" /></div>
              <p className="small muted mt-4">
                Code is open source on <a href={REPO_URL}>GitHub</a>. Found a problem in the data? Open an issue there.
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
