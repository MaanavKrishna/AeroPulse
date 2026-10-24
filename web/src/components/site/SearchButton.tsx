"use client";

import { useSyncExternalStore } from "react";

import styles from "./site.module.css";

export const OPEN_SEARCH = "aeropulse:open-search";

const noop = () => () => {};

export function SearchButton() {
  const mac = useSyncExternalStore(noop, () => /Mac|iPhone|iPad/.test(navigator.platform), () => true);
  return (
    <button type="button" className={styles.searchButton}
            onClick={() => window.dispatchEvent(new Event(OPEN_SEARCH))}>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" strokeWidth="1.8" />
        <path d="m15 15 5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
      <span className={styles.searchLabel}>Search routes and cities</span>
      <kbd>{mac ? "⌘" : "Ctrl"} K</kbd>
    </button>
  );
}
