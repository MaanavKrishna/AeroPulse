"use client";

import { motion } from "motion/react";
import { useId, useMemo, useRef, useState } from "react";

import { levelIndex, ribbonGeometry } from "@/lib/chart";
import { dayMonthYear, monthName, rupees } from "@/lib/format";
import type { CompactPoint, Verdict } from "@/lib/types";

import styles from "./charts.module.css";

const W = 1000, H = 100;
const TONE = ["lv-down", "lv-down", "lv-usual", "lv-up", "lv-up"];

interface Props {
  points: CompactPoint[];
  typical?: Pick<Verdict, "usual_low" | "usual_high"> | null;
  unit?: "inr" | "index";
  size?: "md" | "lg";
  label: string;
  axis?: boolean;
}

/** The fare ribbon: recent prices as a band whose thickness is the 95% range, coloured
 *  from cooler to warmer than this route's own usual. Morphs when the data changes. */
export function FareRibbon({ points, typical = null, unit = "inr", size = "lg", label, axis = true }: Props) {
  const gid = useId().replace(/:/g, "");
  const box = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const geo = useMemo(() => (points.length > 1 ? ribbonGeometry(points, typical, W, H) : null),
    [points, typical]);

  if (!geo) {
    return <div className={`${styles.plot} ${styles[size]} ${styles.empty}`} role="img" aria-label={label}>
      <p>Not enough data to draw this yet.</p></div>;
  }

  const last = points[points.length - 1];
  const lastLevel = levelIndex(last[1], typical?.usual_low ?? null, typical?.usual_high ?? null);
  const fmt = (v: number) => (unit === "inr" ? rupees(v) : v.toFixed(1));
  const ticks = points.map((p, i) => ({ i, d: p[0] })).filter(({ d }) => d.endsWith("-01"));

  const onMove = (e: React.PointerEvent) => {
    const r = box.current?.getBoundingClientRect();
    if (!r) return;
    const i = Math.round(((e.clientX - r.left) / r.width) * (points.length - 1));
    const idx = Math.max(0, Math.min(points.length - 1, i));
    setHover(idx);
  };
  const onKey = (e: React.KeyboardEvent) => {
    const cur = hover ?? points.length - 1;
    const step = e.shiftKey ? 7 : 1;
    let next: number | null = null;
    if (e.key === "ArrowLeft") next = cur - step;
    else if (e.key === "ArrowRight") next = cur + step;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = points.length - 1;
    else if (e.key === "Escape") { setHover(null); return; }
    if (next == null) return;
    e.preventDefault();
    const idx = Math.max(0, Math.min(points.length - 1, next));
    setHover(idx);
  };

  const hp = hover != null ? points[hover] : null;
  const shape = `${points.length}`;      // morph only between series of the same length

  return (
    <div className={`${styles.plot} ${styles[size]} ${axis ? styles.withAxis : ""}`}>
      <div ref={box} className={styles.canvas} role="img" aria-label={label} tabIndex={0}
           aria-roledescription="chart. Use the left and right arrow keys to read values"
           onPointerMove={onMove} onPointerDown={onMove} onPointerLeave={() => setHover(null)}
           onKeyDown={onKey} onBlur={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient id={`g${gid}`} x1="0" x2="1" y1="0" y2="0">
              {geo.stops.map((s, i) => <stop key={i} offset={`${s.offset}%`} stopColor={s.color} />)}
            </linearGradient>
            <clipPath id={`c${gid}`}>
              <motion.rect x="0" y="-20" height={H + 40} initial={{ width: 0 }} animate={{ width: W }}
                           transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.15 }} />
            </clipPath>
          </defs>
          {geo.band && (
            <motion.rect className={styles.band} x="0" width={W} initial={false}
                         animate={{ y: geo.band.y, height: geo.band.h }} transition={{ duration: 0.6 }} />
          )}
          <g clipPath={`url(#c${gid})`}>
            <motion.path key={`a${shape}`} d={geo.area} fill={`url(#g${gid})`} initial={false}
                         animate={{ d: geo.area }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }} />
            <motion.path key={`l${shape}`} d={geo.line} className={styles.line} initial={false}
                         animate={{ d: geo.line }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                         vectorEffect="non-scaling-stroke" />
          </g>
        </svg>
        <div className={styles.overlay}>
          <motion.span className={`${styles.today} ${styles[TONE[lastLevel]]}`}
                       initial={{ opacity: 0, scale: 0.4 }} animate={{ opacity: 1, scale: 1, top: `${geo.y(last[1])}%` }}
                       transition={{ opacity: { delay: 1.1 }, scale: { delay: 1.1 }, top: { duration: 0.7 } }}
                       style={{ left: "100%" }} />
          {axis && ticks.map(({ i, d }) => {
            const left = (i / (points.length - 1)) * 100;
            return left > 4 && left < 96
              ? <span key={d} className={styles.tick} style={{ left: `${left}%` }}>{monthName(d)}</span> : null;
          })}
          {hp && (
            <>
              <motion.span className={styles.cross} initial={false}
                           animate={{ left: `${(hover! / (points.length - 1)) * 100}%` }}
                           transition={{ type: "spring", stiffness: 700, damping: 50 }} />
              <span className={styles.readout} role="status"
                    style={{ left: `${Math.min(Math.max((hover! / (points.length - 1)) * 100, 14), 86)}%`,
                             top: `${Math.max(geo.y(hp[1]) - 8, 0)}%` }}>
                <b>{fmt(hp[1])}</b> on {dayMonthYear(hp[0])}
                {hp[2] != null && hp[3] != null && <><br />95% range {fmt(hp[2])}–{fmt(hp[3]).replace("₹", "")}</>}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
