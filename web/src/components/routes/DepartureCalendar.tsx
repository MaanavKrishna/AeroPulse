import { dayMonth, monthName, weekdayOf } from "@/lib/format";
import type { RouteCalendar } from "@/lib/types";

import styles from "./route.module.css";

const CLS = { above: styles.dayUp, below: styles.dayDown, typical: styles.dayUsual, unknown: styles.dayUnknown };
const WORD = { above: "higher than usual", below: "lower than usual", typical: "usual", unknown: "no fare found" };

/** The next two months of departures, each judged against fares for the same booking window. */
export function DepartureCalendar({ cal }: { cal: RouteCalendar }) {
  if (!cal.days.length) return <p className="muted">No departures priced yet.</p>;
  const lead = weekdayOf(cal.days[0].date);
  return (
    <>
      <div className={styles.calendar} role="table" aria-label="Departure dates compared with the usual fare for that booking window">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => <div key={d} className={styles.dow} role="columnheader">{d}</div>)}
        {Array.from({ length: lead }, (_, i) => <div key={`b${i}`} className={styles.blank} aria-hidden="true" />)}
        {cal.days.map((d) => {
          const first = d.date.endsWith("-01");
          return (
            <div key={d.date} role="cell" title={`${dayMonth(d.date)}: ${WORD[d.level]}`}
                 className={`${styles.day} ${CLS[d.level]} ${first ? styles.monthStart : ""}`}>
              <span>{Number(d.date.slice(8))}{first && ` ${monthName(d.date)}`}</span>
              {d.fare_inr != null && <span className={styles.fare}>₹{(d.fare_inr / 1000).toFixed(1)}k</span>}
              <span className="visually-hidden">{WORD[d.level]}</span>
            </div>
          );
        })}
      </div>
      <ul className="legend">
        <li><span className="swatch sw-cool" />Lower than usual</li>
        <li><span className="swatch sw-even" />Usual</li>
        <li><span className="swatch sw-warm" />Higher than usual</li>
        <li><span className="swatch sw-gap" />No fare found</li>
      </ul>
      <p className="small muted mt-3">As seen on {cal.as_of ? dayMonth(cal.as_of) : "–"}. Each date is compared with fares for the same
        booking window over the last 90 days.{!cal.show_prices && " Individual fares are not shown under our provider's terms."}</p>
    </>
  );
}
