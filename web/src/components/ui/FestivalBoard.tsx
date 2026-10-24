import Link from "next/link";

import { dayMonth, daysBetween } from "@/lib/format";
import type { Festival } from "@/lib/types";

import styles from "./board.module.css";

/** Upcoming festivals as a departures-style board: name, date, days to go, routes followed. */
export function FestivalBoard({ festivals, today }: { festivals: Festival[]; today: string }) {
  return (
    <table className={styles.board}>
      <caption className="visually-hidden">Festivals we follow</caption>
      <thead>
        <tr><th scope="col">Festival</th><th scope="col">Date</th>
          <th scope="col" className={styles.num}>Days to go</th>
          <th scope="col" className={`${styles.num} ${styles.optional}`}>Routes followed</th></tr>
      </thead>
      <tbody>
        {festivals.map((f) => {
          const days = daysBetween(today, f.date);
          return (
            <tr key={f.slug}>
              <th scope="row"><Link href={`/festivals/${f.slug}`}>{f.name}</Link></th>
              <td>{f.date_confirmed ? "" : "around "}{dayMonth(f.date)}</td>
              <td className={`${styles.num} ${styles.strong}`}>{days >= 0 ? days : `${-days} ago`}</td>
              <td className={`${styles.num} ${styles.optional}`}>{f.routes.length}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
