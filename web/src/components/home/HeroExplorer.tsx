"use client";

import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { FareRibbon } from "@/components/charts/FareRibbon";
import { RouteMap } from "@/components/charts/RouteMap";
import { AnimatedRupees } from "@/components/ui/AnimatedRupees";
import { Mark } from "@/components/ui/Verdict";
import { API_URL } from "@/lib/api-url";
import { answer, context, LEVEL_CLASS, shortVerdict, usualRange, windowPhrase } from "@/lib/copy";
import { dayMonth, inr, routeSlug } from "@/lib/format";
import type { Airport, RouteFares, RouteRow, Window } from "@/lib/types";

import styles from "./hero.module.css";

interface Props {
  routes: RouteRow[];
  airports: Airport[];
  windows: Window[];
  initialRoute: string;
  initialWindow: string;
  initialFares: RouteFares;
  asOf: string;
}

const STORE = "aeropulse-route";

/** The home page's answer to "is my fare high today?": pick a route on the form or the chart,
 *  and the answer, the numbers and the 90-day ribbon update in place. */
export function HeroExplorer({ routes, airports, windows, initialRoute, initialWindow, initialFares, asOf }: Props) {
  const [route, setRoute] = useState(initialRoute);
  const [win, setWin] = useState(initialWindow);
  const [fares, setFares] = useState(initialFares);
  const [busy, setBusy] = useState(false);
  const cache = useRef(new Map<string, RouteFares>([[`${initialRoute}|${initialWindow}`, initialFares]]));

  const city = useMemo(() => Object.fromEntries(airports.map((a) => [a.iata, a.city])), [airports]);
  const [origin, dest] = route.split("-");
  const origins = useMemo(() => Array.from(new Set(routes.map((r) => r.origin)))
    .sort((a, b) => city[a].localeCompare(city[b])), [routes, city]);
  const dests = useMemo(() => routes.filter((r) => r.origin === origin).map((r) => r.destination)
    .sort((a, b) => city[a].localeCompare(city[b])), [routes, origin, city]);
  const row = routes.find((r) => r.route === route);

  const load = useCallback(async (nextRoute: string, nextWin: string, remember = true) => {
    setRoute(nextRoute);
    setWin(nextWin);
    const key = `${nextRoute}|${nextWin}`;
    const hit = cache.current.get(key);
    if (hit) setFares(hit);
    else {
      setBusy(true);
      try {
        const res = await fetch(`${API_URL}/v1/routes/${nextRoute}/fares?window=${nextWin}&days=90`);
        if (res.ok) {
          const data = (await res.json()) as RouteFares;
          cache.current.set(key, data);
          setFares(data);
        }
      } finally { setBusy(false); }
    }
    if (remember) {
      try { localStorage.setItem(STORE, JSON.stringify({ route: nextRoute, w: nextWin })); } catch { /* ignore */ }
      history.replaceState(null, "", `/?route=${nextRoute.toLowerCase()}&w=${nextWin}`);
    }
  }, []);

  // A shared link (?route=…) wins; otherwise show the last route this browser looked at.
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const fromUrl = q.get("route")?.toUpperCase();
    const w = q.get("w") ?? undefined;
    if (fromUrl && routes.some((r) => r.route === fromUrl)) {
      // The URL and saved choice exist only in the browser, so they are read after hydration.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (fromUrl !== initialRoute || (w && w !== initialWindow)) load(fromUrl, w ?? initialWindow, false);
      return;
    }
    try {
      const saved = JSON.parse(localStorage.getItem(STORE) ?? "null") as { route: string; w: string } | null;
      if (saved && routes.some((r) => r.route === saved.route) && (saved.route !== initialRoute || saved.w !== initialWindow)) {
        load(saved.route, saved.w, false);
      }
    } catch { /* ignore */ }
  }, [routes, initialRoute, initialWindow, load]);

  const pickOrigin = (o: string) => {
    const options = routes.filter((r) => r.origin === o).map((r) => r.destination);
    load(`${o}-${options.includes(dest) ? dest : options[0]}`, win);
  };
  const swap = () => {
    const back = `${dest}-${origin}`;
    if (routes.some((r) => r.route === back)) load(back, win);
  };

  const v = fares.verdict;
  const key = `${route}|${win}`;

  return (
    <div className={styles.grid}>
      <div className={styles.copy}>
        <h1 className={styles.question}>Is your flight fare high today?</h1>

        <div className={styles.picker} role="group" aria-label="Choose a route">
          <label className={styles.field}>
            <span>From</span>
            <select value={origin} onChange={(e) => pickOrigin(e.target.value)}>
              {origins.map((c) => <option key={c} value={c}>{city[c]} {c}</option>)}
            </select>
          </label>
          <motion.button type="button" className={styles.swap} onClick={swap} whileTap={{ rotate: 180 }}
                         aria-label={`Swap to ${city[dest]} to ${city[origin]}`} title="Swap from and to">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h11m0 0-3.5-3.5M18 7l-3.5 3.5M17 17H6m0 0 3.5 3.5M6 17l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </motion.button>
          <label className={styles.field}>
            <span>To</span>
            <select value={dest} onChange={(e) => load(`${origin}-${e.target.value}`, win)}>
              {dests.map((c) => <option key={c} value={c}>{city[c]} {c}</option>)}
            </select>
          </label>
        </div>

        <div className={styles.whenRow}>
          <span className={styles.whenLabel} id="when-label">Flying</span>
          <LayoutGroup id="when">
            <div className="segments" role="radiogroup" aria-labelledby="when-label">
              {windows.map((w) => (
                <button key={w.key} type="button" role="radio" aria-checked={w.key === win}
                        onClick={() => load(route, w.key)}>
                  {w.key === win && <motion.span layoutId="when-bg" className="seg-bg" />}
                  {w.label.charAt(0).toUpperCase() + w.label.slice(1)}
                </button>
              ))}
            </div>
          </LayoutGroup>
        </div>

        <div className={`${styles.answer} ${LEVEL_CLASS[v.level]}`} aria-live="polite" aria-busy={busy}>
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.div key={key} initial={{ opacity: 0, y: 14, filter: "blur(4px)" }}
                        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                        exit={{ opacity: 0, y: -10, filter: "blur(4px)" }}
                        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
              <span className={`chip ${LEVEL_CLASS[v.level]} ${styles.chip}`}><Mark v={v} />{shortVerdict(v)}</span>
              <p className={styles.answerLine}>{answer(v)}</p>
              <p className={styles.context}>{context(v, win, city[origin], city[dest])}</p>
            </motion.div>
          </AnimatePresence>

          {fares.latest && (
            <dl className="strip">
              <div><dt>Today</dt><dd><AnimatedRupees value={fares.latest.median_inr} /></dd></div>
              <div><dt>Usual</dt><dd>{usualRange(v)}</dd></div>
              <div><dt>Distance</dt><dd>{row ? `${inr(row.distance_km)} km` : "–"}</dd></div>
              <div><dt>Seen</dt><dd>{dayMonth(fares.latest.date)}</dd></div>
            </dl>
          )}

          <div className={styles.ribbon}>
            <FareRibbon points={fares.points} typical={v} size="md"
                        label={`Median cheapest fare, ${city[origin]} to ${city[dest]}, flights ${windowPhrase(win)}, last 90 days. ${answer(v)}`} />
          </div>
          <p className={styles.meta}>
            {fares.latest && <>Today is the median of the cheapest fares on {fares.latest.departure_dates_priced} departure dates. </>}
            The shaded band is what has been usual for 90 days; the ribbon&apos;s thickness is its 95% range.{" "}
            <Link href={`/routes/${routeSlug(route)}?w=${win}`}>Everything about {city[origin]} to {city[dest]}</Link>
          </p>
        </div>
      </div>

      <div className={styles.chart}>
        <RouteMap airports={airports} routes={routes} selected={route} asOf={asOf}
                  onSelect={(r) => load(r, win)} />
        <ul className={styles.key} aria-label="How to read the chart">
          <li><i className={styles.keyDown} />Cheaper than usual</li>
          <li><i className={styles.keyUsual} />Usual</li>
          <li><i className={styles.keyUp} />Dearer than usual</li>
          <li className={styles.keyNote}>Each city pair has two lanes, one per direction. Hover or tap a lane.</li>
        </ul>
      </div>
    </div>
  );
}
