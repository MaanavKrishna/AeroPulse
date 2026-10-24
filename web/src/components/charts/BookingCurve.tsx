"use client";

import { motion, useInView } from "motion/react";
import { useMemo, useRef, useState } from "react";

import { bounds, linear, linePath, niceTicks } from "@/lib/chart";
import { inr } from "@/lib/format";

import styles from "./charts.module.css";

const W = 1000, H = 100;
const MARKS: [number, string][] = [[60, "2 months before"], [30, "1 month"], [14, "2 weeks"], [7, "1 week"], [1, "1 day"]];

interface Props {
  points: { days_ahead: number; value: number }[];
  cheap?: [number, number] | null;
  /** "inr": median fare in rupees. "pct": % against the route's own median. */
  unit: "inr" | "pct";
  label: string;
}

/** Fare by days before departure. Far ahead on the left, departure on the right, the way
 *  time moves for a traveller. Draws itself when it scrolls into view. */
export function BookingCurve({ points, cheap = null, unit, label }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-80px" });
  const [hover, setHover] = useState<number | null>(null);

  const g = useMemo(() => {
    if (points.length < 2) return null;
    const pts = [...points].sort((a, b) => b.days_ahead - a.days_ahead);
    const maxD = pts[0].days_ahead;
    const [lo, hi] = bounds(pts.map((p) => p.value), 0.15);
    const x = linear(maxD, 1, 0, W), y = linear(lo, hi, H, 0);
    const line = linePath(pts.map((p) => x(p.days_ahead)), pts.map((p) => y(p.value)));
    const area = `${line} L${x(pts[pts.length - 1].days_ahead).toFixed(1)},${H} L${x(maxD).toFixed(1)},${H} Z`;
    return { pts, maxD, x, y, line, area, ticks: niceTicks(lo, hi, 3) };
  }, [points]);

  if (!g) return <div className={`${styles.plot} ${styles.md} ${styles.empty}`}><p>Not enough data yet.</p></div>;
  const fmt = (v: number) => (unit === "inr" ? `₹${inr(v)}` : `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(0)}%`);

  const onMove = (e: React.PointerEvent) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const frac = (e.clientX - r.left) / r.width;
    const d = Math.round(g.maxD - frac * (g.maxD - 1));
    const idx = g.pts.findIndex((p) => p.days_ahead === d);
    setHover(idx >= 0 ? idx : null);
  };
  const hp = hover != null ? g.pts[hover] : null;

  return (
    <div className={`${styles.plot} ${styles.md} ${styles.withAxis} ${styles.withY}`}>
      <div ref={ref} className={styles.canvas} role="img" aria-label={label}
           onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
          {cheap && (
            <motion.rect className={styles.cheapZone} x={g.x(cheap[1])} y={0} height={H}
                         initial={{ width: 0 }} animate={seen ? { width: g.x(cheap[0]) - g.x(cheap[1]) } : {}}
                         transition={{ delay: 0.9, duration: 0.5 }} />
          )}
          {g.ticks.map((t) => <line key={t} className={styles.gridLine} x1={0} x2={W} y1={g.y(t)} y2={g.y(t)} vectorEffect="non-scaling-stroke" />)}
          {unit === "pct" && <line className={styles.zero} x1={0} x2={W} y1={g.y(0)} y2={g.y(0)} vectorEffect="non-scaling-stroke" />}
          <motion.path d={g.area} className={styles.curveArea} initial={{ opacity: 0 }}
                       animate={seen ? { opacity: 1 } : {}} transition={{ delay: 0.5, duration: 0.6 }} />
          <motion.path d={g.line} className={styles.curveLine} vectorEffect="non-scaling-stroke"
                       initial={{ pathLength: 0 }} animate={seen ? { pathLength: 1 } : {}}
                       transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }} />
        </svg>
        <div className={styles.overlay}>
          {g.ticks.map((t) => <span key={t} className={styles.ylabel} style={{ top: `${g.y(t)}%` }}>{fmt(t)}</span>)}
          {MARKS.filter(([d]) => d <= g.maxD).map(([d, text]) => {
            const left = (g.x(d) / W) * 100;
            const edge = left < 8 ? styles.edgeStart : left > 92 ? styles.edgeEnd : "";
            return <span key={d} className={`${styles.tick} ${edge}`} style={{ left: `${left}%` }}>{text}</span>;
          })}
          {cheap && <span className={styles.zoneLabel} style={{ left: `${((g.x(cheap[0]) + g.x(cheap[1])) / 2 / W) * 100}%` }}>usually cheapest</span>}
          {hp && (
            <>
              <span className={styles.cross} style={{ left: `${(g.x(hp.days_ahead) / W) * 100}%` }} />
              <span className={styles.readout} role="status"
                    style={{ left: `${Math.min(Math.max((g.x(hp.days_ahead) / W) * 100, 14), 86)}%`, top: `${Math.max(g.y(hp.value) - 8, 0)}%` }}>
                <b>{fmt(hp.value)}</b> {hp.days_ahead} {hp.days_ahead === 1 ? "day" : "days"} before
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
