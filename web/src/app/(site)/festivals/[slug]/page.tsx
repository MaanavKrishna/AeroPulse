import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { FestivalTrack } from "@/components/charts/FestivalTrack";
import { CopyButton } from "@/components/ui/CopyButton";
import { PageHead } from "@/components/ui/PageHead";
import { SectionHead } from "@/components/ui/SectionHead";
import { getFestival, getFestivals, getMeta } from "@/lib/api";
import { dayMonth, dayMonthYear, routeSlug, rupees } from "@/lib/format";
import { SITE_URL } from "@/lib/site";

import styles from "./festival.module.css";

export async function generateStaticParams() {
  return (await getFestivals()).map((f) => ({ slug: f.slug }));
}

export async function generateMetadata({ params }: PageProps<"/festivals/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const f = await getFestival(slug);
  return f ? { title: `${f.festival} ${f.date.slice(0, 4)} flight fares`,
               description: `How ${f.festival} travel fares compare with ordinary weeks on India's busiest festival routes.` }
           : { title: "Festival not found" };
}

async function Festival({ params }: { params: PageProps<"/festivals/[slug]">["params"] }) {
  const { slug } = await params;
  const [f, meta] = await Promise.all([getFestival(slug), getMeta()]);
  if (!f) notFound();
  const routes = f.routes.map((r) => ({ ...r, latest: r.points.at(-1) })).filter((r) => r.latest)
    .sort((a, b) => (b.latest!.pct_vs_ordinary ?? -1e9) - (a.latest!.pct_vs_ordinary ?? -1e9));
  const top = routes[0];
  const year = f.date.slice(0, 4);
  const cite = `AeroPulse, "${f.festival} ${year} fares", ${meta.latest_date ? dayMonthYear(meta.latest_date) : ""}. ${SITE_URL}/festivals/${slug}${meta.data_mode === "demo" ? " [DEMO DATA]" : ""}`;

  return (
    <>
      <PageHead icon="lamp" crumbs={<><Link href="/festivals">Festivals</Link> / {f.festival} {year}</>}
                title={`${f.festival} ${year} fares`}
                lede={`${f.date_confirmed ? "" : "Around "}${dayMonthYear(f.date)}. We follow the cheapest fare for flying on ${dayMonth(f.peak_departure)}, two days before, as it is seen each day.`}>
        {top?.latest?.pct_vs_ordinary != null && (
          <div className={styles.headline}>
            <span className="chip lv-up">▲ {top.latest.pct_vs_ordinary.toFixed(0)}% above ordinary weeks</span>
            <p className={styles.big}>{top.name} is the dearest festival route so far.</p>
            <p className={styles.sub}>The cheapest fare for {dayMonth(f.peak_departure)} is {top.latest.pct_vs_ordinary.toFixed(0)}% above ordinary
              dates at {top.latest.days_ahead} days ahead{f.show_prices && top.latest.fare_inr ? ` (${rupees(top.latest.fare_inr)})` : ""}, as seen on {dayMonth(top.latest.date)}.</p>
          </div>
        )}
      </PageHead>
      <div className="wrap page-body">
        <SectionHead icon="route" title="Route by route" aside="Shaded area: how far above ordinary weeks the festival fare sits" />
        {routes.length ? (
          <div className={styles.grid}>
            {routes.map((r) => (
              <article key={r.route} className="card">
                <h3 className={styles.routeName}><Link href={`/routes/${routeSlug(r.route)}`}>{r.name}</Link></h3>
                <p className={styles.routeState}>
                  {r.latest!.pct_vs_ordinary != null
                    ? <><span className="chip lv-up">+{r.latest!.pct_vs_ordinary.toFixed(0)}%</span> {r.latest!.days_ahead} days ahead</>
                    : "No comparison yet"}
                </p>
                <FestivalTrack points={r.points} label={`${r.name}: festival fare against ordinary weeks, by days before departure`} />
              </article>
            ))}
          </div>
        ) : (
          <div className="empty"><h2>Not tracked yet</h2><p>We start following festival fares about two months before.</p></div>
        )}
        <section className="section">
          <SectionHead icon="data" title="Cite this" />
          <pre className="snippet">{cite}</pre>
          <div className="actions mt-3"><CopyButton text={cite} label="Copy citation" /></div>
        </section>
      </div>
    </>
  );
}

export default function FestivalPage(props: PageProps<"/festivals/[slug]">) {
  return (
    <Suspense fallback={<div className="sign sign-band"><div className="wrap page-head"><p>Loading…</p></div></div>}>
      <Festival params={props.params} />
    </Suspense>
  );
}
