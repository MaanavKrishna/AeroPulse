"use client";

import { motion, useInView } from "motion/react";
import { useRef } from "react";

import { WEEKDAY_NAMES } from "@/lib/copy";
import type { WeekdayEffect } from "@/lib/types";

import styles from "./charts.module.css";

/** How the cheapest fare differs by the day you fly, against the usual for the same
 *  booking distance. Bars grow from zero when they scroll into view. */
export function WeekdayBars({ data, label }: { data: WeekdayEffect[]; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-60px" });
  if (data.length < 3) return <p className="muted">Not enough data yet.</p>;
  const max = Math.max(...data.map((d) => Math.abs(d.pct_vs_typical)), 5);
  const cheapest = data.reduce((a, b) => (b.pct_vs_typical < a.pct_vs_typical ? b : a));
  const dearest = data.reduce((a, b) => (b.pct_vs_typical > a.pct_vs_typical ? b : a));

  return (
    <div ref={ref} className={styles.weekdays} role="img" aria-label={label}>
      {data.map((d, i) => {
        const h = (Math.abs(d.pct_vs_typical) / max) * 50;
        const up = d.pct_vs_typical >= 0;
        const isMin = d === cheapest, isMax = d === dearest;
        return (
          <div key={d.weekday} className={styles.weekday}>
            <span className={`${styles.wdValue} ${isMin ? "tone-down" : isMax ? "tone-up" : ""}`}>
              {d.pct_vs_typical >= 0 ? "+" : "−"}{Math.abs(d.pct_vs_typical).toFixed(0)}%
            </span>
            <div className={styles.wdTrack}>
              <motion.span className={`${styles.wdBar} ${up ? styles.wdUp : styles.wdDown}`}
                           style={{ [up ? "bottom" : "top"]: "50%" }}
                           initial={{ height: 0 }} animate={seen ? { height: `${h}%` } : {}}
                           transition={{ delay: 0.08 * i, type: "spring", stiffness: 160, damping: 20 }} />
            </div>
            <span className={styles.wdName} title={WEEKDAY_NAMES[d.weekday]}>{d.weekday}</span>
          </div>
        );
      })}
    </div>
  );
}
