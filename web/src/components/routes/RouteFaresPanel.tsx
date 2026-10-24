"use client";

import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";

import { FareRibbon } from "@/components/charts/FareRibbon";
import { AnimatedRupees } from "@/components/ui/AnimatedRupees";
import { Mark } from "@/components/ui/Verdict";
import { API_URL } from "@/lib/api-url";
import { answer, context, LEVEL_CLASS, shortVerdict, usualRange, windowPhrase } from "@/lib/copy";
import { dayMonth, rupees } from "@/lib/format";
import type { RouteDetail, RouteFares } from "@/lib/types";

import styles from "./route.module.css";

const RANGES: [string, string, number | null][] = [["90", "90 days", 90], ["365", "1 year", 365], ["all", "All", null]];

/** Booking-window tabs, the answer for the chosen window, and its fare history. */
export function RouteFaresPanel({ detail, initial, initialWindow, header }: {
  detail: RouteDetail; initial: RouteFares; initialWindow: string; header: React.ReactNode;
}) {
  const [win, setWin] = useState(initialWindow);
  const [range, setRange] = useState("90");
  const [fares, setFares] = useState(initial);
  const cache = useRef(new Map([[`${initialWindow}|90`, initial]]));
  const from = detail.origin.city, to = detail.destination.city;

  const load = useCallback(async (w: string, r: string) => {
    setWin(w); setRange(r);
    history.replaceState(null, "", `?w=${w}${r !== "90" ? `&range=${r}` : ""}`);
    const key = `${w}|${r}`;
    const hit = cache.current.get(key);
    if (hit) { setFares(hit); return; }
    const days = RANGES.find(([k]) => k === r)?.[2];
    const res = await fetch(`${API_URL}/v1/routes/${detail.route}/fares?window=${w}${days ? `&days=${days}` : ""}`);
    if (res.ok) { const data = (await res.json()) as RouteFares; cache.current.set(key, data); setFares(data); }
  }, [detail.route]);

  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const w = q.get("w"), r = q.get("range");
    if ((w && w !== initialWindow && detail.windows.some((x) => x.window === w)) || (r && r !== "90")) {
      // The URL and saved choice exist only in the browser, so they are read after hydration.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      load(w ?? initialWindow, r ?? "90");
    }
  }, [detail.windows, initialWindow, load]);

  const v = fares.verdict;
  return (
    <>
    <div className="sign sign-band">
    <div className={`wrap ${styles.head}`}>
      {header}
      <LayoutGroup id="windows">
        <div className={styles.windows} role="tablist" aria-label="How far ahead you are flying">
          {detail.windows.map((w) => (
            <button key={w.window} type="button" role="tab" aria-selected={w.window === win}
                    className={`${styles.windowTab} ${LEVEL_CLASS[w.verdict.level]}`} onClick={() => load(w.window, range)}>
              {w.window === win && <motion.span layoutId="window-active" className={styles.windowActive} />}
              <span className={styles.wLabel}>{w.label.charAt(0).toUpperCase() + w.label.slice(1)}</span>
              <span className={styles.wState}><Mark v={w.verdict} />{shortVerdict(w.verdict)}</span>
              {w.median_cheapest_fare_inr != null && <span className={styles.wFare}>{rupees(w.median_cheapest_fare_inr)}</span>}
            </button>
          ))}
        </div>
      </LayoutGroup>

      <div className={`${styles.answer} ${LEVEL_CLASS[v.level]}`} aria-live="polite">
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.div key={win} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}>
            <span className={`chip ${LEVEL_CLASS[v.level]} ${styles.chip}`}><Mark v={v} />{shortVerdict(v)}</span>
            <p className={styles.answerLine}>{answer(v)}</p>
            <p className={styles.context}>{context(v, win, from, to)}</p>
          </motion.div>
        </AnimatePresence>
        {fares.latest && (
          <dl className="strip">
            <div><dt>Today</dt><dd><AnimatedRupees value={fares.latest.median_inr} /></dd></div>
            <div><dt>Usual, last 90 days</dt><dd>{usualRange(v)}</dd></div>
            <div><dt>Cheapest to dearest date</dt><dd>{rupees(fares.latest.lowest_inr)}–{rupees(fares.latest.highest_inr).slice(1)}</dd></div>
            <div><dt>Departure dates priced</dt><dd>{fares.latest.departure_dates_priced}, seen {dayMonth(fares.latest.date)}</dd></div>
          </dl>
        )}
      </div>
    </div>
    </div>

    <div className="wrap">
      <div className={styles.historyHead}>
        <h2>How fares have moved, flying {windowPhrase(win)}</h2>
        <LayoutGroup id="range">
          <div className="segments" role="radiogroup" aria-label="Time range">
            {RANGES.map(([k, label]) => (
              <button key={k} type="button" role="radio" aria-checked={range === k}
                      onClick={() => load(win, k)}>
                {range === k && <motion.span layoutId="range-bg" className="seg-bg" />}{label}
              </button>
            ))}
          </div>
        </LayoutGroup>
      </div>
      <div className="card"><FareRibbon points={fares.points} typical={v} size="lg"
                  label={`Median cheapest fare, ${from} to ${to}, flights ${windowPhrase(win)}. ${answer(v)}`} /></div>
      <ul className="legend">
        <li><span className="swatch sw-band" />Usual range (middle half of the last 90 days)</li>
        <li><span className="swatch sw-cool" />Lower than usual</li>
        <li><span className="swatch sw-warm" />Higher than usual</li>
        <li>Ribbon thickness: 95% range of the estimate. Use ← → on the chart to read values.</li>
      </ul>
    </div>
    </>
  );
}
