"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";

import { CHART_MARGIN, greatCircleKm, lane, projection } from "@/lib/chart";
import { shortVerdict } from "@/lib/copy";
import { inr, routeSlug } from "@/lib/format";
import type { Airport, Level, RouteRow } from "@/lib/types";

import styles from "./map.module.css";

const LEVEL: Record<Level, string> = { above: styles.up, below: styles.down, typical: styles.usual, unknown: styles.unknown };

/** Where each airport's label sits, so names keep clear of airways and each other. */
const LABELS: Record<string, [number, number, "start" | "end"]> = {
  SXR: [8, 4, "start"], DEL: [9, -9, "start"], LKO: [8, -8, "start"], PAT: [8, -8, "start"],
  CCU: [-9, -9, "end"], AMD: [-9, 4, "end"], BOM: [-9, 4, "end"], PNQ: [9, 13, "start"],
  HYD: [9, 4, "start"], GOI: [-9, 4, "end"], BLR: [-9, 12, "end"], MAA: [9, 8, "start"],
  COK: [-9, 6, "end"],
};

interface Props {
  airports: Airport[];
  routes: RouteRow[];
  selected?: string | null;
  /** Called when a route is picked on the map; without it, routes are links. */
  onSelect?: (route: string) => void;
  /** Airport page: emphasise routes touching this airport. */
  focus?: string;
  asOf?: string;
  compact?: boolean;
}

/** An aeronautical en-route chart of every tracked route. No coastline or borders: the
 *  graticule and airports carry the geography, and borders are not ours to draw. */
export function RouteMap({ airports, routes, selected = null, onSelect, focus, asOf, compact = false }: Props) {
  const calm = useReducedMotion();
  const box = useRef<HTMLDivElement>(null);
  const [hot, setHot] = useState<{ route: RouteRow; x: number; y: number; w: number } | null>(null);

  const byCode = useMemo(() => Object.fromEntries(airports.map((a) => [a.iata, a])), [airports]);
  const used = useMemo(() => airports.filter((a) =>
    routes.some((r) => r.origin === a.iata || r.destination === a.iata)), [airports, routes]);
  const proj = useMemo(() => projection(used), [used]);
  const vw = proj.width + CHART_MARGIN * 2, vh = proj.height + CHART_MARGIN * 2;

  const lanes = useMemo(() => routes
    .filter((r) => byCode[r.origin] && byCode[r.destination])
    .map((r, i) => ({ r, i, l: lane(proj, byCode[r.origin], byCode[r.destination]) }))
    .sort((a, b) => Number(a.r.route === selected) - Number(b.r.route === selected)),
  [routes, byCode, proj, selected]);

  const sel = lanes.find((x) => x.r.route === selected);
  const left = CHART_MARGIN, top = CHART_MARGIN, right = CHART_MARGIN + proj.width, bottom = CHART_MARGIN + proj.height;
  const latLines = range(proj.lat0, proj.lat1), lonLines = range(proj.lon0, proj.lon1);
  const bar = 500 / (111.2 / 26);

  const point = (e: React.PointerEvent) => {
    const r = box.current?.getBoundingClientRect();
    return r ? { x: e.clientX - r.left, y: e.clientY - r.top, w: r.width } : { x: 0, y: 0, w: 400 };
  };

  return (
    <figure ref={box} className={`${styles.map} ${compact ? styles.compact : ""} ${selected ? styles.hasSelection : ""} ${hot ? styles.hovering : ""}`}>
      <svg viewBox={`0 0 ${vw.toFixed(0)} ${vh.toFixed(0)}`} role="group"
           aria-label="Route chart of tracked domestic routes, coloured by fares against usual">
        <g className={styles.graticule} aria-hidden="true">
          {latLines.map((lat) => {
            const y = proj.xy(lat, proj.lon0)[1];
            return (
              <g key={`lat${lat}`}>
                {lat % 5 === 0 && <line className={styles.grid} x1={left} x2={right} y1={y} y2={y} />}
                {lat % 5 === 0 && <text className={styles.deg} x={left - 6} y={y + 3.5} textAnchor="end">{lat}°N</text>}
                <line className={styles.tick} x1={left} x2={left + 4} y1={y} y2={y} />
                <line className={styles.tick} x1={right - 4} x2={right} y1={y} y2={y} />
              </g>
            );
          })}
          {lonLines.map((lon) => {
            const x = proj.xy(proj.lat0, lon)[0];
            return (
              <g key={`lon${lon}`}>
                {lon % 5 === 0 && <line className={styles.grid} x1={x} x2={x} y1={top} y2={bottom} />}
                {lon % 5 === 0 && <text className={styles.deg} x={x} y={bottom + 16} textAnchor="middle">{lon}°E</text>}
                <line className={styles.tick} x1={x} x2={x} y1={top} y2={top + 4} />
                <line className={styles.tick} x1={x} x2={x} y1={bottom - 4} y2={bottom} />
              </g>
            );
          })}
          <rect className={styles.neatline} x={left} y={top} width={proj.width} height={proj.height} />
        </g>

        <g>
          {lanes.map(({ r, i, l }) => {
            const isSel = r.route === selected;
            const dim = focus ? !(r.origin === focus || r.destination === focus) : false;
            const isHot = hot?.route.route === r.route;
            return (
              <motion.line key={r.route} x1={l.x0} y1={l.y0} x2={l.x1} y2={l.y1}
                           className={`${styles.airway} ${LEVEL[r.verdict.level]} ${isSel ? styles.selected : ""} ${dim ? styles.dim : ""} ${isHot ? styles.hot : ""}`}
                           initial={calm ? false : { pathLength: 0 }} animate={{ pathLength: 1 }}
                           transition={{ duration: 0.9, delay: 0.2 + (i % 40) * 0.018, ease: [0.16, 1, 0.3, 1] }} />
            );
          })}
        </g>

        <g aria-hidden="true">
          {used.map((a, k) => {
            const [x, y] = proj.xy(a.lat, a.lon);
            const [dx, dy, anchor] = LABELS[a.iata] ?? [8, 4, "start"];
            const isEnd = sel && (sel.r.origin === a.iata || sel.r.destination === a.iata);
            return (
              <motion.g key={a.iata} className={`${styles.airport} ${isEnd || focus === a.iata ? styles.end : ""}`}
                        initial={calm ? false : { opacity: 0, scale: 0.4 }} animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.05 + k * 0.035, type: "spring", stiffness: 420, damping: 22 }}
                        style={{ transformOrigin: `${x}px ${y}px` }}>
                <circle cx={x} cy={y} r={3.6} />
                {[[0, -1], [1, 0], [0, 1], [-1, 0]].map(([ux, uy]) => (
                  <line key={`${ux}${uy}`} x1={x + ux * 3.6} y1={y + uy * 3.6} x2={x + ux * 6.2} y2={y + uy * 6.2} />
                ))}
                <text x={x + dx} y={y + dy} textAnchor={anchor}>
                  <tspan className={styles.iata}>{a.iata}</tspan>
                  {!compact && <tspan className={styles.city} x={x + dx} dy={10.5}>{a.city} {a.icao}</tspan>}
                </text>
              </motion.g>
            );
          })}
        </g>

        {!compact && (
          <g className={styles.titleBlock} aria-hidden="true">
            <rect x={right - 180} y={bottom - 74} width={170} height={64} />
            <text className={styles.tbTitle} x={right - 171} y={bottom - 57}>AeroPulse route chart</text>
            <text className={styles.tbText} x={right - 171} y={bottom - 44}>Airways coloured by fares vs usual</text>
            <text className={styles.tbText} x={right - 171} y={bottom - 32}>{asOf}</text>
            <line className={styles.scale} x1={right - 171} x2={right - 171 + bar} y1={bottom - 21} y2={bottom - 21} />
            {[0, 0.5, 1].map((f) => (
              <line key={f} className={styles.scale} x1={right - 171 + bar * f} x2={right - 171 + bar * f}
                    y1={bottom - (f === 0.5 ? 23 : 24)} y2={bottom - (f === 0.5 ? 19 : 18)} />
            ))}
            <text className={styles.tbText} x={right - 166 + bar} y={bottom - 18}>500 km</text>
          </g>
        )}

        <AnimatePresence>
          {sel && (
            <motion.g key={sel.r.route} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      transition={{ delay: 0.4, duration: 0.4 }} aria-hidden="true">
              <SelectedMarks lane={sel.l} km={greatCircleKm(byCode[sel.r.origin], byCode[sel.r.destination])}
                             cls={LEVEL[sel.r.verdict.level]} calm={!!calm} />
            </motion.g>
          )}
        </AnimatePresence>

        <g>
          {lanes.map(({ r, l }) => {
            const props = {
              className: styles.hit,
              onPointerMove: (e: React.PointerEvent) => setHot({ route: r, ...point(e) }),
              onPointerLeave: () => setHot(null),
              onFocus: () => {
                const box2 = box.current?.getBoundingClientRect();
                const s = box2 ? box2.width / vw : 1;
                setHot({ route: r, x: ((l.x0 + l.x1) / 2) * s, y: ((l.y0 + l.y1) / 2) * s, w: box2?.width ?? 400 });
              },
              onBlur: () => setHot(null),
            };
            const label = `${r.name}: ${shortVerdict(r.verdict)}`;
            const lineEl = <line x1={l.x0} y1={l.y0} x2={l.x1} y2={l.y1} />;
            return onSelect ? (
              <a key={r.route} href={`/routes/${routeSlug(r.route)}`} aria-label={label} {...props}
                 onClick={(e) => { if (e.metaKey || e.ctrlKey || e.shiftKey) return; e.preventDefault(); setHot(null); onSelect(r.route); }}>
                {lineEl}
              </a>
            ) : (
              <Link key={r.route} href={`/routes/${routeSlug(r.route)}`} aria-label={label} {...props}>{lineEl}</Link>
            );
          })}
        </g>
      </svg>
      <AnimatePresence>
        {hot && (
          <motion.div className={styles.tip} role="status" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }} transition={{ duration: 0.12 }}
                      style={{ left: Math.min(Math.max(hot.x, 90), hot.w - 90), top: hot.y }}>
            <b>{hot.route.name}</b>
            <span>{shortVerdict(hot.route.verdict)}, {inr(hot.route.distance_km)} km</span>
          </motion.div>
        )}
      </AnimatePresence>
    </figure>
  );
}

function SelectedMarks({ lane: l, km, cls, calm }: { lane: ReturnType<typeof lane>; km: number; cls: string; calm: boolean }) {
  let angle = l.angle;
  if (angle > 90) angle -= 180;
  else if (angle < -90) angle += 180;
  const tx = (l.x0 + l.x1) / 2 + l.normal[0] * 9, ty = (l.y0 + l.y1) / 2 + l.normal[1] * 9 + 3;
  const len = Math.hypot(l.x1 - l.x0, l.y1 - l.y0);
  return (
    <>
      <text className={`${styles.distance} ${cls}`} x={tx} y={ty} textAnchor="middle" transform={`rotate(${angle.toFixed(1)} ${tx} ${ty})`}>
        {inr(km)} km
      </text>
      {!calm && (
        <motion.path d="M4,0 L-3,-3 L-1.6,0 L-3,3 Z" className={styles.plane}
                     initial={{ x: l.x0, y: l.y0, rotate: l.angle }}
                     animate={{ x: [l.x0, l.x1], y: [l.y0, l.y1], rotate: l.angle }}
                     transition={{ duration: Math.max(len / 26, 4), repeat: Infinity, ease: "linear" }} />
      )}
    </>
  );
}

function range(a: number, b: number) {
  return Array.from({ length: b - a + 1 }, (_, i) => a + i);
}
