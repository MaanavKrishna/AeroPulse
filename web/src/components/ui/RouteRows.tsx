import Link from "next/link";
import { ViewTransition } from "react";

import { Sparkline } from "@/components/charts/Sparkline";
import { shortVerdict } from "@/lib/copy";
import { inr, routeSlug } from "@/lib/format";
import type { RouteRow } from "@/lib/types";

import styles from "./ui.module.css";
import { VerdictChip } from "./Verdict";

/** A ruled list of routes: codes, names, 90-day sparkline, verdict. The codes morph into
 *  the route page title when you open one. */
export function RouteRows({ rows, showDistance = false }: { rows: RouteRow[]; showDistance?: boolean }) {
  return (
    <ul className={`${styles.rows} card card-flush`}>
      {rows.map((r) => (
        <li key={r.route}>
          <Link className={styles.row} href={`/routes/${routeSlug(r.route)}`}>
            <ViewTransition name={`route-${routeSlug(r.route)}`}>
              <span className={styles.codes}><span>{r.origin}</span><i aria-hidden="true" /><span>{r.destination}</span></span>
            </ViewTransition>
            <span className={styles.name}>
              {r.name}
              {showDistance && <small>{inr(r.distance_km)} km</small>}
            </span>
            <Sparkline points={r.series} typical={r.verdict} label={`Last 90 days, ${r.name}: ${shortVerdict(r.verdict)}`} />
            <span className={styles.state}><VerdictChip v={r.verdict} /></span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
