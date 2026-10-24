"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { MultiLine, SERIES_COLORS } from "@/components/charts/MultiLine";
import { VerdictChip } from "@/components/ui/Verdict";
import { inr, routeSlug, signedPct } from "@/lib/format";
import type { RouteRow } from "@/lib/types";

import styles from "./compare.module.css";

const MAX = 4;

/** Pick up to four routes; their indices share one chart, rebased to 100 on the first day. */
export function CompareTool({ routes, initial }: { routes: RouteRow[]; initial: string[] }) {
  const [picked, setPicked] = useState<string[]>(initial);
  const [adding, setAdding] = useState("");

  useEffect(() => {
    const q = new URLSearchParams(location.search).get("routes");
    if (q) {
      const ids = q.toUpperCase().split(",").filter((id) => routes.some((r) => r.route === id)).slice(0, MAX);
      // The URL and saved choice exist only in the browser, so they are read after hydration.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (ids.length) setPicked(ids);
    }
  }, [routes]);

  useEffect(() => {
    history.replaceState(null, "", `?routes=${picked.join(",")}`);
  }, [picked]);

  const rows = useMemo(() => picked.map((id) => routes.find((r) => r.route === id)!).filter(Boolean), [picked, routes]);
  const options = routes.filter((r) => !picked.includes(r.route)).sort((a, b) => a.name.localeCompare(b.name));

  const add = (id: string) => { if (id && picked.length < MAX) setPicked([...picked, id]); setAdding(""); };
  const remove = (id: string) => setPicked(picked.filter((p) => p !== id));

  return (
    <>
      <div className={styles.picker}>
        <AnimatePresence initial={false}>
          {rows.map((r, k) => (
            <motion.span key={r.route} className={styles.pick} layout initial={{ opacity: 0, scale: 0.8 }}
                         animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }}>
              <i style={{ background: SERIES_COLORS[k % 4] }} />
              {r.name}
              <button type="button" onClick={() => remove(r.route)} aria-label={`Remove ${r.name}`}>×</button>
            </motion.span>
          ))}
        </AnimatePresence>
        {picked.length < MAX && (
          <label className={styles.add}>
            <span className="visually-hidden">Add a route</span>
            <select value={adding} onChange={(e) => add(e.target.value)}>
              <option value="">+ Add a route</option>
              {options.map((r) => <option key={r.route} value={r.route}>{r.name}</option>)}
            </select>
          </label>
        )}
      </div>

      <div className="card mt-5">
        <MultiLine lines={rows.map((r) => ({ id: r.route, label: r.name, points: r.series }))}
                   label={`Route indices compared: ${rows.map((r) => r.name).join(", ")}`} />
      </div>

      <div className="card card-flush mt-5">
        <table className={`table ${styles.table}`}>
          <thead>
            <tr><th>Route</th><th>Today</th><th>90-day change</th><th>Distance</th><th /></tr>
          </thead>
          <tbody>
            {rows.map((r, k) => {
              const first = r.series[0]?.[1], last = r.series.at(-1)?.[1];
              return (
                <tr key={r.route}>
                  <td><span className={styles.dot} style={{ background: SERIES_COLORS[k % 4] }} />
                    <Link href={`/routes/${routeSlug(r.route)}`}>{r.name}</Link></td>
                  <td><VerdictChip v={r.verdict} /></td>
                  <td>{first && last ? signedPct((last / first - 1) * 100) : "–"}</td>
                  <td>{inr(r.distance_km)} km</td>
                  <td><button type="button" className={styles.remove} onClick={() => remove(r.route)}>Remove</button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
