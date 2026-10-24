"use client";

import { AnimatePresence, motion } from "motion/react";
import { useId, useState } from "react";

import styles from "./faq.module.css";

/** Questions that open smoothly in place; one at a time. */
export function Faq({ items }: { items: { q: string; a: React.ReactNode }[] }) {
  const [open, setOpen] = useState<number | null>(0);
  const base = useId();
  return (
    <div className={styles.faq}>
      {items.map((item, i) => {
        const isOpen = open === i;
        return (
          <div key={item.q} className={`${styles.item} ${isOpen ? styles.open : ""}`}>
            <h3>
              <button type="button" aria-expanded={isOpen} aria-controls={`${base}-${i}`}
                      onClick={() => setOpen(isOpen ? null : i)}>
                {item.q}
                <motion.span className={styles.icon} animate={{ rotate: isOpen ? 45 : 0 }} aria-hidden="true">+</motion.span>
              </button>
            </h3>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div id={`${base}-${i}`} className={styles.answer}
                            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}>
                  <div className={styles.answerInner}>{item.a}</div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
