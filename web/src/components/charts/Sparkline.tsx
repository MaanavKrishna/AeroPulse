import { levelIndex, ribbonGeometry } from "@/lib/chart";
import type { CompactPoint, Verdict } from "@/lib/types";

import styles from "./charts.module.css";

const TONE = ["lv-down", "lv-down", "lv-usual", "lv-up", "lv-up"];

/** A small static ribbon for lists. Server-rendered; no interaction. */
export function Sparkline({ points, typical, label }: {
  points: CompactPoint[]; typical: Pick<Verdict, "usual_low" | "usual_high">; label: string;
}) {
  if (points.length < 2) return <span className={styles.sparkEmpty}>No data yet</span>;
  const geo = ribbonGeometry(points, typical, 200, 40);
  const id = `s${points.length}${points[0][0].replace(/-/g, "")}${Math.round(points[points.length - 1][1] * 100)}`;
  const last = points[points.length - 1];
  const lv = levelIndex(last[1], typical.usual_low, typical.usual_high);
  return (
    <span className={styles.spark} role="img" aria-label={label}>
      <svg viewBox="0 0 200 40" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id={id} x1="0" x2="1" y1="0" y2="0">
            {geo.stops.filter((_, i) => i % 3 === 0 || i === geo.stops.length - 1)
              .map((s, i) => <stop key={i} offset={`${s.offset}%`} stopColor={s.color} />)}
          </linearGradient>
        </defs>
        {geo.band && <rect className={styles.band} x="0" y={geo.band.y} width="200" height={geo.band.h} />}
        <path d={geo.area} fill={`url(#${id})`} />
        <path d={geo.line} className={styles.line} vectorEffect="non-scaling-stroke" />
      </svg>
      <span className={`${styles.sparkDot} ${styles[TONE[lv]]}`} style={{ top: `${(geo.y(last[1]) / 40) * 100}%` }} />
    </span>
  );
}
