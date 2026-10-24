"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

/** Copies text; the label flips to "Copied" and back. */
export function CopyButton({ text, label }: { text: string; label: string }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1600);
    } catch { /* clipboard blocked; the text is visible to select by hand */ }
  };
  return (
    <button type="button" className="btn btn-quiet" onClick={copy} aria-live="polite">
      <AnimatePresence mode="wait" initial={false}>
        <motion.span key={done ? "done" : "idle"} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
                     exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.15 }}>
          {done ? "Copied" : label}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
