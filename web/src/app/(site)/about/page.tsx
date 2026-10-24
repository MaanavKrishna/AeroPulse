import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHead } from "@/components/ui/PageHead";
import { Pictogram } from "@/components/ui/Pictogram";
import { SectionHead } from "@/components/ui/SectionHead";
import { getMeta, getSources } from "@/lib/api";
import { REPO_URL } from "@/lib/site";

import styles from "./about.module.css";

export const metadata: Metadata = {
  title: "About AeroPulse",
  description: "Who AeroPulse is for, where the fares come from, what we never collect, and how to help.",
};

const AUDIENCES = [
  { icon: "departures" as const, title: "Travellers", text: "See in one glance whether today's fare is high, low or ordinary for your route, and when it is usually cheapest." },
  { icon: "book" as const, title: "Journalists", text: "Check a claim about festival fares or price spikes against a public, citable series, with charts you can embed." },
  { icon: "data" as const, title: "Researchers", text: "Download every number as CSV, read the method, and rebuild the index from the open code." },
];

async function Demo() {
  const meta = await getMeta();
  if (meta.data_mode !== "demo") return null;
  return (
    <section className="section" id="demo" aria-labelledby="h-demo">
      <div className={styles.demo}>
        <Pictogram name="info" size={34} />
        <div>
          <h2 id="h-demo">You are looking at demo data</h2>
          <p>
            Real fare collection has not started yet. Until it does, AeroPulse runs on fares made by a generator so the site
            can be built and tested in the open. They follow realistic patterns, so the charts behave like the real thing, but
            they are not prices anyone could buy. Every page says so, and the downloads are marked too.
          </p>
        </div>
      </div>
    </section>
  );
}

async function Sources() {
  const s = await getSources();
  const real = s.providers.filter((p) => p.name !== "demo");
  return (
    <>
      <section className="section" id="sources" aria-labelledby="h-sources">
        <SectionHead id="h-sources" icon="data" title="Where fares come from" />
        <ul className={styles.sources}>
          {real.map((p) => (
            <li key={p.name} className="card">
              <div className={styles.sourceTop}>
                <h3>{p.homepage ? <a href={p.homepage}>{p.display_name}</a> : p.display_name}</h3>
                <span className={`chip ${p.terms_reviewed ? styles.reviewed : ""}`}>
                  {p.terms_reviewed ? "Terms reviewed" : "Terms under review"}
                </span>
              </div>
              <p className={styles.kind}>{p.kind}</p>
              <p className="muted mt-2">{p.notes}</p>
              <p className="small mt-3">
                {p.raw_redistribution ? "Raw fares may be shared." : "Raw fares are not redistributed; only summaries are published."}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="section" id="never" aria-labelledby="h-never">
        <SectionHead id="h-never" icon="shield" title="What we never collect" />
        <ul className={styles.never}>
          {s.never_collected.map((n) => (
            <li key={n}><span className={styles.cross} aria-hidden="true">×</span>{n}</li>
          ))}
        </ul>
      </section>
    </>
  );
}

export default function AboutPage() {
  return (
    <>
      <PageHead icon="info" title="About AeroPulse"
                lede="An open index of Indian domestic airfares. It tells you whether a fare is high, low or ordinary, and shows its working." />
      <div className="wrap page-body">
        <section aria-labelledby="h-who">
          <SectionHead id="h-who" icon="pin" title="Who it's for" />
          <ul className={styles.audiences}>
            {AUDIENCES.map((a) => (
              <li key={a.title} className="card">
                <span className="sign-tile"><Pictogram name={a.icon} size={22} /></span>
                <h3>{a.title}</h3>
                <p>{a.text}</p>
              </li>
            ))}
          </ul>
        </section>

        <Suspense fallback={null}><Demo /><Sources /></Suspense>

        <section className="section" aria-labelledby="h-help">
          <SectionHead id="h-help" icon="route" title="Help build it" />
          <div className={`card ${styles.help}`}>
            <p>
              AeroPulse is open source. The code, the method and the data are all public, and anyone can suggest a route,
              report a wrong number or improve the site.
            </p>
            <div className={styles.helpLinks}>
              <a className="btn btn-primary" href={REPO_URL}>See the code on GitHub</a>
              <a className="btn btn-quiet" href={`${REPO_URL}/issues/new`}>Report a problem</a>
              <Link className="btn btn-quiet" href="/methodology">Read the method</Link>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}
