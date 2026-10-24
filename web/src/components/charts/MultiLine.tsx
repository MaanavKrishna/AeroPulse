"use client";

import { AnimatePresence, motion } from "motion/react";
import { useMemo, useRef, useState } from "react";

import { bounds, linear, linePath, niceTicks } from "@/lib/chart";
import { dayMonthYear, monthName } from "@/lib/format";
import type { CompactPoint } from "@/lib/types";

import styles from "./charts.module.css";

const W = 1000, H = 100;
export const SERIES_COLORS = ["var(--cat-1)", "var(--cat-2)", "var(--cat-3)", "var(--cat-4)"];

export interface Line { id: string; label: string; points: CompactPoint[] }

/** Several index lines on one chart, rebased so each starts at 100 on the first shared day.
 *  Lines draw in; adding or removing one animates. */
export function MultiLine({ lines, label, rebase = true }: { lines: Line[]; label: string; rebase?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const g = useMemo(() => {
    if (!lines.length) return null;
    const dates = Array.from(new Set(lines.flatMap((l) => l.points.map((p) => p[0])))).sort();
    const shared = dates.filter((d) => lines.every((l) => l.points.some((p) => p[0] === d)));
    const axis = shared.length > 1 ? shared : dates;
    const series = lines.map((l) => {
      const byDate = new Map(l.points.map((p) => [p[0], p[1]]));
      const base = rebase ? byDate.get(axis[0]) ?? 100 : 100;
      return { ...l, values: axis.map((d) => ((byDate.get(d) ?? NaN) / base) * 100) };
    });
    const all = series.flatMap((s) => s.values.filter(Number.isFinite));
    const [lo, hi] = bounds(all, 0.1);
    const x = linear(0, Math.max(axis.length - 1, 1), 0, W), y = linear(lo, hi, H, 0);
    return { axis, series, x, y, ticks: niceTicks(lo, hi, 3) };
  }, [lines, rebase]);

  if (!g || g.axis.length < 2) return <div className={`${styles.plot} ${styles.lg} ${styles.empty}`}><p>Pick at least one route.</p></div>;

  const onMove = (e: React.PointerEvent) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r) return;
    const i = Math.round(((e.clientX - r.left) / r.width) * (g.axis.length - 1));
    setHover(Math.max(0, Math.min(g.axis.length - 1, i)));
  };

  return (
    <div className={`${styles.plot} ${styles.lg} ${styles.withAxis} ${styles.withY}`}>
      <div ref={ref} className={styles.canvas} role="img" aria-label={label}
           onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
          {g.ticks.map((t) => <line key={t} className={styles.gridLine} x1={0} x2={W} y1={g.y(t)} y2={g.y(t)} vectorEffect="non-scaling-stroke" />)}
          <AnimatePresence>
            {g.series.map((s, k) => {
              const pts = s.values.map((v, i) => [g.x(i), Number.isFinite(v) ? g.y(v) : NaN] as const)
                .filter(([, yy]) => Number.isFinite(yy));
              const d = linePath(pts.map((p) => p[0]), pts.map((p) => p[1]));
              return (
                <motion.path key={s.id} d={d} fill="none" stroke={SERIES_COLORS[k % 4]} strokeWidth={2}
                             vectorEffect="non-scaling-stroke" strokeLinejoin="round"
                             initial={{ pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: 1, d }}
                             exit={{ opacity: 0 }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} />
              );
            })}
          </AnimatePresence>
        </svg>
        <div className={styles.overlay}>
          {g.ticks.map((t) => <span key={t} className={styles.ylabel} style={{ top: `${g.y(t)}%` }}>{t.toFixed(0)}</span>)}
          {g.axis.map((d, i) => d.endsWith("-01") && i > 2 && i < g.axis.length - 3
            ? <span key={d} className={styles.tick} style={{ left: `${(i / (g.axis.length - 1)) * 100}%` }}>{monthName(d)}</span> : null)}
          {hover != null && (
            <>
              <span className={styles.cross} style={{ left: `${(hover / (g.axis.length - 1)) * 100}%` }} />
              <span className={styles.readout} role="status"
                    style={{ left: `${Math.min(Math.max((hover / (g.axis.length - 1)) * 100, 16), 84)}%`, top: 0 }}>
                <b>{dayMonthYear(g.axis[hover])}</b>
                {g.series.map((s, k) => Number.isFinite(s.values[hover]) && (
                  <span key={s.id} className={styles.readoutRow}>
                    <i style={{ background: SERIES_COLORS[k % 4] }} />{s.label} {s.values[hover].toFixed(1)}
                  </span>
                ))}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
