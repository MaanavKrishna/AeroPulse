"use client";

import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { LEVEL_CLASS, MARK, shortVerdict } from "@/lib/copy";
import { routeSlug } from "@/lib/format";
import type { Airport, RouteRow } from "@/lib/types";

import { OPEN_SEARCH } from "./SearchButton";
import styles from "./site.module.css";

interface Item {
  id: string;
  kind: "Route" | "Airport" | "Page";
  title: string;
  detail: string;
  href: string;
  haystack: string;
  mark?: { text: string; cls: string };
}

const PAGES: [string, string, string][] = [
  ["/", "Home", "is my fare high today"],
  ["/routes", "All routes", "list every route explorer"],
  ["/airports", "Airports", "cities"],
  ["/trends", "Trends", "national index movers best time to book weekday"],
  ["/festivals", "Festival fares", "diwali chhath holi christmas"],
  ["/compare", "Compare routes", "side by side chart"],
  ["/guide", "How to read AeroPulse", "help faq usual ribbon glossary"],
  ["/methodology", "Method", "jevons index uncertainty how it is measured"],
  ["/data", "Downloads and API", "csv dataset export"],
  ["/status", "Collection status", "health uptime"],
  ["/about", "About and ethics", "sources privacy"],
];

/** Search routes, airports and pages from anywhere: ⌘K, Ctrl+K or "/". */
export function CommandPalette({ routes, airports }: { routes: RouteRow[]; airports: Airport[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const restore = useRef<HTMLElement | null>(null);

  const items = useMemo<Item[]>(() => {
    const byCode = Object.fromEntries(airports.map((a) => [a.iata, a]));
    const words = (code: string) => {
      const a = byCode[code];
      return a ? `${a.city} ${a.iata} ${a.icao} ${(a.aliases ?? []).join(" ")}` : code;
    };
    return [
      ...routes.map((r) => ({
        id: `r-${r.route}`, kind: "Route" as const, title: r.name,
        detail: `${r.origin} to ${r.destination}, ${shortVerdict(r.verdict).toLowerCase()}`,
        href: `/routes/${routeSlug(r.route)}`,
        haystack: `${words(r.origin)} to ${words(r.destination)} ${r.origin}-${r.destination} ${r.origin}${r.destination}`.toLowerCase(),
        mark: { text: MARK[r.verdict.level], cls: LEVEL_CLASS[r.verdict.level] },
      })),
      ...airports.map((a) => ({
        id: `a-${a.iata}`, kind: "Airport" as const, title: `${a.city} (${a.iata})`,
        detail: `${a.airport}, ${a.icao}`, href: `/airports/${a.iata.toLowerCase()}`,
        haystack: `${words(a.iata)} ${a.airport} ${a.state}`.toLowerCase(),
      })),
      ...PAGES.map(([href, title, words]) => ({
        id: `p-${href}`, kind: "Page" as const, title, detail: href, href,
        haystack: `${title} ${words}`.toLowerCase(),
      })),
    ];
  }, [routes, airports]);

  const results = useMemo(() => {
    const terms = query.toLowerCase().replace(/[→>-]/g, " ").split(/\s+/).filter(Boolean)
      .filter((t) => t !== "to");
    if (!terms.length) return items.filter((i) => i.kind !== "Route").slice(0, 8)
      .concat(items.filter((i) => i.kind === "Route").slice(0, 6));
    return items.filter((i) => terms.every((t) => i.haystack.includes(t))).slice(0, 12);
  }, [items, query]);

  const show = useCallback(() => {
    restore.current = document.activeElement as HTMLElement | null;
    setQuery(""); setActive(0); setOpen(true);
  }, []);
  const hide = useCallback(() => { setOpen(false); restore.current?.focus?.(); }, []);
  const go = useCallback((item: Item | undefined) => {
    if (!item) return;
    setOpen(false);
    router.push(item.href);
  }, [router]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLElement && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
        e.preventDefault(); show();
      }
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener(OPEN_SEARCH, show);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener(OPEN_SEARCH, show); };
  }, [show]);

  useEffect(() => { if (open) requestAnimationFrame(() => input.current?.focus()); }, [open]);

  const onInputKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((i) => Math.min(i + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); go(results[active]); }
    else if (e.key === "Escape") { e.preventDefault(); hide(); }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div className={styles.paletteBackdrop} onMouseDown={hide}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}>
          <motion.div role="dialog" aria-modal="true" aria-label="Search AeroPulse"
                      className={styles.palette} onMouseDown={(e) => e.stopPropagation()}
                      initial={{ opacity: 0, y: -12, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.98 }}
                      transition={{ type: "spring", stiffness: 520, damping: 38 }}>
            <input ref={input} className={styles.paletteInput} value={query} onKeyDown={onInputKey}
                   onChange={(e) => { setQuery(e.target.value); setActive(0); }}
                   placeholder="Try “Bangalore to Kolkata”, “GOI” or “festival”"
                   role="combobox" aria-expanded="true" aria-controls="palette-results"
                   aria-activedescendant={results[active]?.id} aria-autocomplete="list" />
            <ul id="palette-results" role="listbox" className={styles.paletteList}>
              {results.length === 0 && <li className={styles.paletteEmpty}>Nothing matches “{query}”. Try a city name or an airport code.</li>}
              {results.map((item, i) => (
                <li key={item.id} id={item.id} role="option" aria-selected={i === active}
                    className={styles.paletteItem} onMouseEnter={() => setActive(i)}
                    onClick={() => go(item)}>
                  {i === active && <motion.span layoutId="palette-active" className={styles.paletteActive}
                                                transition={{ type: "spring", stiffness: 600, damping: 40 }} />}
                  <span className={styles.paletteKind}>{item.kind}</span>
                  <span className={styles.paletteTitle}>
                    {item.mark && <span className={`mark ${item.mark.cls}`} aria-hidden="true">{item.mark.text}</span>}
                    {item.title}
                  </span>
                  <span className={styles.paletteDetail}>{item.detail}</span>
                </li>
              ))}
            </ul>
            <p className={styles.paletteHint}>↑ ↓ to move, Enter to open, Esc to close</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
