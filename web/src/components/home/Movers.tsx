"use client";

import { motion, useInView } from "motion/react";
import Link from "next/link";
import { useRef } from "react";

import { routeSlug, signedPct } from "@/lib/format";
import { Pictogram } from "@/components/ui/Pictogram";
import type { Mover } from "@/lib/types";

import styles from "./movers.module.css";

/** Two ruled columns: routes whose index rose and fell most this week. Bars scale with the
 *  move and grow in when the section scrolls into view. */
export function Movers({ up, down }: { up: Mover[]; down: Mover[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useInView(ref, { once: true, margin: "-60px" });
  const max = Math.max(...[...up, ...down].map((m) => Math.abs(m.change_pct)), 1);
  const column = (title: string, list: Mover[], tone: "up" | "down") => (
    <div>
      <h3 className={`${styles.title} ${tone === "up" ? "tone-up" : "tone-down"}`}><Pictogram name={tone === "up" ? "departures" : "arrivals"} size={18} />{title}</h3>
      <ol className={styles.list}>
        {list.map((m, i) => (
          <li key={m.route_id}>
            <Link href={`/routes/${routeSlug(m.route_id)}`} className={styles.item}>
              <span className={styles.name}>{m.name}</span>
              <span className={`${styles.value} ${tone === "up" ? "tone-up" : "tone-down"}`}>{signedPct(m.change_pct)}</span>
              <span className={styles.track} aria-hidden="true">
                <motion.span className={`${styles.bar} ${tone === "up" ? styles.up : styles.down}`}
                             initial={{ scaleX: 0 }} animate={seen ? { scaleX: Math.abs(m.change_pct) / max } : {}}
                             transition={{ delay: 0.06 * i, type: "spring", stiffness: 140, damping: 20 }} />
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
  return (
    <div ref={ref} className="split">
      {column("Rose most", up, "up")}
      {column("Fell most", down, "down")}
    </div>
  );
}
