import Link from "next/link";

import { AirportSymbol } from "@/components/ui/AirportSymbol";

import { Nav } from "./Nav";
import { SearchButton } from "./SearchButton";
import styles from "./site.module.css";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className={`${styles.head} sign`}>
      <div className={`wrap ${styles.headInner}`}>
        <Link className={styles.wordmark} href="/" aria-label="AeroPulse home">
          <span className={styles.logoTile}><AirportSymbol size={18} /></span>
          <span>AeroPulse</span>
        </Link>
        <Nav />
        <div className={styles.tools}>
          <SearchButton />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
