import Link from "next/link";

import { getMeta } from "@/lib/api";

import styles from "./site.module.css";

/** Shown on every page while any published number is synthetic. */
export async function DemoNotice() {
  const meta = await getMeta();
  if (meta.data_mode !== "demo") return null;
  return (
    <div className={styles.notice} role="note">
      <div className="wrap">
        <p>
          <strong>Demo data.</strong> Every fare on this site is synthetic until real collection
          starts. <Link href="/about#demo">What that means</Link>
        </p>
      </div>
    </div>
  );
}
