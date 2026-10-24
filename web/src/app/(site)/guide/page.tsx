import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { FareRibbon } from "@/components/charts/FareRibbon";
import { Faq } from "@/components/ui/Faq";
import { PageHead } from "@/components/ui/PageHead";
import { Pictogram } from "@/components/ui/Pictogram";
import { SectionHead } from "@/components/ui/SectionHead";
import { getMeta, getRouteFares } from "@/lib/api";
import { answer, usualRange } from "@/lib/copy";
import { rupees } from "@/lib/format";

import styles from "./guide.module.css";

export const metadata: Metadata = {
  title: "How to read AeroPulse",
  description: "A two-minute guide: what “usual” means, how to read the fare ribbon, booking windows, and what AeroPulse does not do.",
};

const FAQ = [
  { q: "Is this a prediction of where fares will go?",
    a: <p>No. Everything on AeroPulse describes what fares have done. When we say a route is usually cheapest five weeks
      out, that is what the last month looked like, not a promise about next month. We never say &ldquo;book now&rdquo;.</p> },
  { q: "Why the cheapest fare, and not the average?",
    a: <><p>The cheapest fare is what a careful traveller can actually buy, and it is what booking sites show first. It moves
      quickly when cheap seats sell out, which is exactly what you want to know before booking.</p>
      <p>It is not what the average passenger paid. The Consumer Price Index airfare item is closer to that. The two usually
        move together but can differ.</p></> },
  { q: "What does “usual” mean exactly?",
    a: <p>For each route and booking window we take the last 90 days and keep the middle half: the 25th to 75th percentile.
      Fares inside that band are &ldquo;usual&rdquo;. Above it is &ldquo;higher than usual&rdquo;, below it &ldquo;lower than usual&rdquo;.
      Until a route has 21 days of history we don&apos;t give a verdict.</p> },
  { q: "Why are there four booking windows?",
    a: <p>A fare two days before departure and a fare two months before are different things. Mixing them would hide what
      matters, so each window gets its own verdict: within a week, 1–2 weeks, 2–4 weeks and 1–2 months out.</p> },
  { q: "Where do the fares come from? Do you scrape airlines?",
    a: <p>Only from licensed fare APIs used within their terms. We never scrape airline or travel-agency sites, never work
      around bot checks, and never collect anything about travellers. <Link href="/about">More on sources and ethics</Link>.</p> },
  { q: "Can I use these numbers in an article or research?",
    a: <p>Yes, under CC BY 4.0: credit AeroPulse with a link. Every route page has a ready-made citation, a CSV, a chart image
      and embed code. The full dataset is on the <Link href="/data">data page</Link>.</p> },
  { q: "Why does the site say “demo data”?",
    a: <p>Until real collection starts, the site runs on synthetic fares made by a generator, so it can be built and tested.
      They look realistic on purpose, but they are not real prices, and every page says so.</p> },
];

const GLOSSARY: [string, string][] = [
  ["Route", "One direction between two airports. Delhi to Mumbai and Mumbai to Delhi are two routes."],
  ["Booking window", "How far ahead of departure a fare was seen: within a week, 1–2 weeks, 2–4 weeks or 1–2 months."],
  ["Cheapest fare", "The lowest economy one-way fare the provider found for one departure date."],
  ["Today's fare", "The median of the cheapest fares across the departure dates in a booking window, seen today."],
  ["Usual range", "The middle half of the last 90 days for that route and window."],
  ["Index", "A number that starts at 100 and moves with fares, so routes with different prices can be compared."],
  ["95% range", "How much today's number could move if different departure dates had been priced. Drawn as the ribbon's thickness."],
];

async function Anatomy() {
  const fares = await getRouteFares("DEL-BOM", "15-30");
  if (!fares) return null;
  const v = fares.verdict;
  const callouts = [
    { n: 1, title: "The grey band is usual", text: `For this route and window: ${usualRange(v)}. Anything inside it is ordinary.` },
    { n: 2, title: "Colour shows where fares sit", text: "Blue when fares are below usual, orange above, grey in between." },
    { n: 3, title: "Thickness is uncertainty", text: "A thick ribbon means the day's number rests on fewer or more spread-out fares." },
    { n: 4, title: "The dot is today", text: fares.latest ? `Today: ${rupees(fares.latest.median_inr)}. ${answer(v)}` : answer(v) },
  ];
  return (
    <div className={styles.anatomy}>
      <div className="card">
        <p className={styles.example}>Example: Delhi to Mumbai, flying 2–4 weeks out</p>
        <FareRibbon points={fares.points} typical={v} size="lg" label="Example fare ribbon, Delhi to Mumbai" />
      </div>
      <ol className={styles.callouts}>
        {callouts.map((c) => (
          <li key={c.n}><span className={styles.num}>{c.n}</span><div><h3>{c.title}</h3><p>{c.text}</p></div></li>
        ))}
      </ol>
    </div>
  );
}

async function DemoNote() {
  const meta = await getMeta();
  return meta.data_mode === "demo"
    ? <p className="small muted mt-3">The example uses demo data while real collection has not started.</p> : null;
}

export default function GuidePage() {
  return (
    <>
      <PageHead icon="book" title="How to read AeroPulse"
                lede="Two minutes, and you will know what every chart on this site is telling you." />
      <div className="wrap page-body">
        <section aria-labelledby="h-anatomy">
          <SectionHead id="h-anatomy" icon="index" title="The fare ribbon, piece by piece" />
          <Suspense fallback={null}><Anatomy /><DemoNote /></Suspense>
        </section>

        <section className="section" aria-labelledby="h-windows">
          <SectionHead id="h-windows" icon="clock" title="Booking windows" aside="Each route gets a verdict for each" />
          <ul className={styles.windows}>
            {[["Within a week", "1–7 days", "Last-minute fares. Usually the dearest, and the most volatile."],
              ["1–2 weeks out", "8–14 days", "Short notice. Prices are already climbing on busy routes."],
              ["2–4 weeks out", "15–30 days", "The window most people book in. Our default view."],
              ["1–2 months out", "31–60 days", "Early booking. Often the cheapest, but not always."]].map(([t, d, x]) => (
              <li key={t} className="card"><Pictogram name="calendar" size={26} /><h3>{t}</h3><p className={styles.days}>{d} before departure</p><p>{x}</p></li>
            ))}
          </ul>
        </section>

        <section className="section" aria-labelledby="h-faq">
          <SectionHead id="h-faq" icon="info" title="Questions people ask" />
          <Faq items={FAQ} />
        </section>

        <section className="section" aria-labelledby="h-gloss">
          <SectionHead id="h-gloss" icon="book" title="Glossary" />
          <dl className={styles.glossary}>
            {GLOSSARY.map(([t, d]) => <div key={t} className="card"><dt>{t}</dt><dd>{d}</dd></div>)}
          </dl>
        </section>
      </div>
    </>
  );
}
