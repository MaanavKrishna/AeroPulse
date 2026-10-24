"use client";

import { LayoutGroup, motion } from "motion/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV } from "@/lib/site";

import styles from "./site.module.css";

/** Main navigation. The underline slides to the current section. */
export function Nav() {
  const path = usePathname();
  return (
    <nav className={styles.nav} aria-label="Main">
      <LayoutGroup id="nav">
        {NAV.map(({ href, label }) => {
          const current = path === href || path.startsWith(`${href}/`);
          return (
            <Link key={href} href={href} aria-current={current ? "page" : undefined}>
              {label}
              {current && <motion.span layoutId="nav-underline" className={styles.underline} />}
            </Link>
          );
        })}
      </LayoutGroup>
    </nav>
  );
}
