"use client";

import { motion, useReducedMotion } from "motion/react";

import { AirportSymbol } from "@/components/ui/AirportSymbol";
import { inr } from "@/lib/format";
import type { Airport, Level } from "@/lib/types";

import styles from "./route.module.css";

const TONE: Record<Level, string> = { above: styles.legUp, below: styles.legDown, typical: "", unknown: "" };

/** The route as one leg between two airport symbols: the line draws, then a plane flies it. */
export function RouteLeg({ origin, destination, km, level }: { origin: Airport; destination: Airport; km: number; level: Level }) {
  const calm = useReducedMotion();
  return (
    <div className={styles.leg}>
      <div className={styles.end}>
        <span className={styles.code}>{origin.iata}</span>
        <span className={styles.endName}>{origin.airport}, {origin.icao}</span>
      </div>
      <div className={styles.legMid} aria-hidden="true">
        <span className={styles.legKm}>{inr(km)} km great-circle</span>
        <div className={styles.legLine}>
          <AirportSymbol size={16} />
          <div className={styles.legTrack}>
            <motion.span className={`${styles.legPath} ${TONE[level]}`} initial={calm ? false : { scaleX: 0 }}
                         animate={{ scaleX: 1 }} transition={{ duration: 1.1, ease: [0.65, 0, 0.35, 1], delay: 0.15 }} />
            {!calm && (
              <motion.svg className={styles.legPlane} viewBox="-6 -6 12 12" initial={{ left: "0%", opacity: 0 }}
                          animate={{ left: ["0%", "100%"], opacity: [0, 1, 1, 0] }}
                          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1.2, times: [0, 0.1, 0.9, 1] }}>
                <path d="M6,0 L-4.5,-4.5 L-2.3,0 L-4.5,4.5 Z" />
              </motion.svg>
            )}
          </div>
          <AirportSymbol size={16} />
        </div>
      </div>
      <div className={`${styles.end} ${styles.endRight}`}>
        <span className={styles.code}>{destination.iata}</span>
        <span className={styles.endName}>{destination.airport}, {destination.icao}</span>
      </div>
    </div>
  );
}
