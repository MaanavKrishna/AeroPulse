import Link from "next/link";

import { API_URL } from "@/lib/api";
import { REPO_URL } from "@/lib/site";

import styles from "./site.module.css";

const COLUMNS = [
  { title: "Explore", links: [["/routes", "All routes"], ["/airports", "Airports"], ["/trends", "Trends"],
    ["/festivals", "Festival fares"], ["/compare", "Compare routes"]] },
  { title: "Understand", links: [["/guide", "How to read AeroPulse"], ["/methodology", "Method"],
    ["/status", "Collection status"], ["/about", "About and ethics"]] },
  { title: "Use the data", links: [["/data", "Downloads"], ["/data#api", "API"], [`${API_URL}/v1/docs`, "API reference"],
    [REPO_URL, "Source code"]] },
] as const;

export function Footer() {
  return (
    <footer className={`${styles.foot} sign`}>
      <div className={`wrap ${styles.footInner}`}>
        <div className={styles.footLead}>
          <p><strong>AeroPulse</strong> is an open record of Indian domestic airfares. It describes
            what fares have done; it does not predict them.</p>
          <p className="small muted mt-3">Data and text CC BY 4.0. Code AGPL-3.0.</p>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title}>
            <h2>{col.title}</h2>
            <ul>
              {col.links.map(([href, label]) => (
                <li key={href}>
                  {href.startsWith("http") ? <a href={href}>{label}</a> : <Link href={href}>{label}</Link>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </footer>
  );
}
