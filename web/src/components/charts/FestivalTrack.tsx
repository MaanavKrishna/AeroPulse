"use client";

import { motion, useInView } from "motion/react";
import { useRef } from "react";

import { linear, linePath } from "@/lib/chart";

import styles from "./charts.module.css";

const W = 1000, H = 100;

/** The peak-day fare, as % above ordinary dates booked the same distance ahead, by days
 *  before departure. Draws in when visible. */
export function FestivalTrack({ points, label }: {
  points: { days_ahead: number; pct_vs_ordinary: number | null }[]; label: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-40px" });
  const pts = points.filter((p): p is { days_ahead: number; pct_vs_ordinary: number } => p.pct_vs_ordinary != null)
    .sort((a, b) => b.days_ahead - a.days_ahead);
  if (pts.length < 2) return <div className={`${styles.plot} ${styles.sm} ${styles.empty}`}><p>Not enough data yet.</p></div>;
  const maxD = Math.max(pts[0].days_ahead, 30);
  let lo = Math.min(...pts.map((p) => p.pct_vs_ordinary), -10), hi = Math.max(...pts.map((p) => p.pct_vs_ordinary), 10);
  const pad = (hi - lo) * 0.08; lo -= pad; hi += pad;
  const x = linear(maxD, 1, 0, W), y = linear(lo, hi, H, 0);
  const line = linePath(pts.map((p) => x(p.days_ahead)), pts.map((p) => y(p.pct_vs_ordinary)));
  const zero = y(0);
  const area = `${line} L${x(pts[pts.length - 1].days_ahead)},${zero} L${x(pts[0].days_ahead)},${zero} Z`;
  const last = pts[pts.length - 1];
  const grid = [50, 100, 150].filter((v) => v < hi);

  return (
    <div className={`${styles.plot} ${styles.sm} ${styles.withAxis} ${styles.withY}`}>
      <div ref={ref} className={styles.canvas} role="img" aria-label={label}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
          {grid.map((v) => <line key={v} className={styles.gridLine} x1={0} x2={W} y1={y(v)} y2={y(v)} vectorEffect="non-scaling-stroke" />)}
          <line className={styles.zero} x1={0} x2={W} y1={zero} y2={zero} vectorEffect="non-scaling-stroke" />
          <motion.path d={area} className={styles.trackArea} initial={{ opacity: 0 }} animate={seen ? { opacity: 1 } : {}}
                       transition={{ delay: 0.6, duration: 0.5 }} />
          <motion.path d={line} className={styles.trackLine} vectorEffect="non-scaling-stroke"
                       initial={{ pathLength: 0 }} animate={seen ? { pathLength: 1 } : {}}
                       transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }} />
        </svg>
        <div className={styles.overlay}>
          <span className={styles.ylabel} style={{ top: `${zero}%` }}>usual</span>
          {grid.map((v) => <span key={v} className={styles.ylabel} style={{ top: `${y(v)}%` }}>+{v}%</span>)}
          <motion.span className={`${styles.today} ${styles["lv-up"]}`} style={{ left: `${(x(last.days_ahead) / W) * 100}%`, top: `${y(last.pct_vs_ordinary)}%` }}
                       initial={{ scale: 0 }} animate={seen ? { scale: 1 } : {}} transition={{ delay: 1.1 }} />
          {[[30, "30 days before"], [14, "14"], [7, "7"], [1, "1 day"]].map(([d, t]) => (
            <span key={d} className={styles.tick} style={{ left: `${(x(Number(d)) / W) * 100}%` }}>{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
