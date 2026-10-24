"use client";

import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Sparkline } from "@/components/charts/Sparkline";
import { VerdictChip } from "@/components/ui/Verdict";
import { shortVerdict } from "@/lib/copy";
import { inr, routeSlug } from "@/lib/format";
import type { Airport, RouteRow } from "@/lib/types";

import ui from "@/components/ui/ui.module.css";
import styles from "./explorer.module.css";

type Sort = "above" | "below" | "name" | "distance";
type Level = "all" | "above" | "typical" | "below";

const SORTS: [Sort, string][] = [["above", "Most above usual"], ["below", "Most below usual"], ["name", "A to Z"], ["distance", "Longest"]];
const LEVELS: [Level, string][] = [["all", "All"], ["above", "Above usual"], ["typical", "Usual"], ["below", "Below usual"]];

/** Every route, filterable by city and level, sortable. Rows glide to their new places. */
export function RouteExplorer({ routes, airports }: { routes: RouteRow[]; airports: Airport[] }) {
  const [sort, setSort] = useState<Sort>("above");
  const [level, setLevel] = useState<Level>("all");
  const [city, setCity] = useState("");
  const [q, setQ] = useState("");

  const counts = useMemo(() => ({
    above: routes.filter((r) => r.verdict.level === "above").length,
    typical: routes.filter((r) => r.verdict.level === "typical").length,
    below: routes.filter((r) => r.verdict.level === "below").length,
  }), [routes]);

  const shown = useMemo(() => {
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const list = routes.filter((r) =>
      (level === "all" || r.verdict.level === level) &&
      (!city || r.origin === city || r.destination === city) &&
      terms.every((t) => `${r.name} ${r.route}`.toLowerCase().includes(t)));
    const by: Record<Sort, (a: RouteRow, b: RouteRow) => number> = {
      above: (a, b) => (b.verdict.pct_vs_usual ?? 0) - (a.verdict.pct_vs_usual ?? 0),
      below: (a, b) => (a.verdict.pct_vs_usual ?? 0) - (b.verdict.pct_vs_usual ?? 0),
      name: (a, b) => a.name.localeCompare(b.name),
      distance: (a, b) => b.distance_km - a.distance_km,
    };
    return [...list].sort(by[sort]);
  }, [routes, sort, level, city, q]);

  return (
    <>
      <div className={styles.summary}>
        <p><b className="tone-up">{counts.above}</b> routes above usual</p>
        <p><b>{counts.typical}</b> about usual</p>
        <p><b className="tone-down">{counts.below}</b> below usual</p>
      </div>

      <div className={styles.controls}>
        <label className={styles.search}>
          <span className="visually-hidden">Filter routes</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter, e.g. “Goa” or “BLR”" />
        </label>
        <label className={styles.city}>
          <span>City</span>
          <select value={city} onChange={(e) => setCity(e.target.value)}>
            <option value="">All cities</option>
            {airports.map((a) => <option key={a.iata} value={a.iata}>{a.city}</option>)}
          </select>
        </label>
        <LayoutGroup id="level">
          <div className="segments" role="radiogroup" aria-label="Show">
            {LEVELS.map(([k, label]) => (
              <button key={k} type="button" role="radio" aria-checked={level === k}
                      onClick={() => setLevel(k)}>
                {level === k && <motion.span layoutId="level-bg" className="seg-bg" />}{label}
              </button>
            ))}
          </div>
        </LayoutGroup>
        <LayoutGroup id="sort">
          <div className="segments" role="radiogroup" aria-label="Sort">
            {SORTS.map(([k, label]) => (
              <button key={k} type="button" role="radio" aria-checked={sort === k}
                      onClick={() => setSort(k)}>
                {sort === k && <motion.span layoutId="sort-bg" className="seg-bg" />}{label}
              </button>
            ))}
          </div>
        </LayoutGroup>
      </div>

      <p className="small muted" aria-live="polite">{shown.length} of {routes.length} routes</p>
      <ul className={`${ui.rows} ${styles.list} card card-flush`}>
        <AnimatePresence initial={false}>
          {shown.map((r) => (
            <motion.li key={r.route} layout="position" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                       exit={{ opacity: 0 }} transition={{ type: "spring", stiffness: 500, damping: 42 }}>
              <Link className={ui.row} href={`/routes/${routeSlug(r.route)}`}>
                <span className={ui.codes}><span>{r.origin}</span><i aria-hidden="true" /><span>{r.destination}</span></span>
                <span className={ui.name}>{r.name}<small>{inr(r.distance_km)} km</small></span>
                <Sparkline points={r.series} typical={r.verdict} label={`Last 90 days, ${r.name}: ${shortVerdict(r.verdict)}`} />
                <span className={ui.state}><VerdictChip v={r.verdict} /></span>
              </Link>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
      {shown.length === 0 && (
        <div className="empty mt-5"><h2>No routes match</h2><p>Clear the filter or pick another city.</p></div>
      )}
    </>
  );
}
