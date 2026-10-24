"use client";

import { MotionConfig } from "motion/react";

/** Every animation on the site follows the reader's reduced-motion setting. */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user" transition={{ type: "spring", stiffness: 380, damping: 36 }}>
      {children}
    </MotionConfig>
  );
}
