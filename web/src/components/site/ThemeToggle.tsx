"use client";

import { AnimatePresence, motion } from "motion/react";
import { useSyncExternalStore } from "react";

import styles from "./site.module.css";

type Theme = "light" | "dark";

function currentTheme(): Theme {
  const set = document.documentElement.dataset.theme;
  if (set === "light" || set === "dark") return set;
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const THEME_EVENT = "aeropulse:theme";

function subscribe(onChange: () => void) {
  const media = matchMedia("(prefers-color-scheme: dark)");
  media.addEventListener("change", onChange);
  window.addEventListener(THEME_EVENT, onChange);
  return () => { media.removeEventListener("change", onChange); window.removeEventListener(THEME_EVENT, onChange); };
}

export function ThemeToggle() {
  // null on the server: the icon appears once the browser knows the theme.
  const theme = useSyncExternalStore<Theme | null>(subscribe, currentTheme, () => null);

  const toggle = () => {
    const next: Theme = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("aeropulse-theme", next); } catch { /* storage blocked */ }
    window.dispatchEvent(new Event(THEME_EVENT));
  };

  return (
    <button type="button" className={styles.iconButton} onClick={toggle}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.svg key={theme ?? "none"} viewBox="0 0 24 24" aria-hidden="true"
                    initial={{ rotate: -60, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 60, opacity: 0 }} transition={{ duration: 0.2 }}>
          {theme === "dark" ? (
            <g fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <circle cx="12" cy="12" r="4.2" />
              <path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" />
            </g>
          ) : (
            <path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z" fill="currentColor" />
          )}
        </motion.svg>
      </AnimatePresence>
    </button>
  );
}
