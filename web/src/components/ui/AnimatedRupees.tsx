"use client";

import { animate, motion, useMotionValue, useTransform } from "motion/react";
import { useEffect, useRef } from "react";

import { rupees } from "@/lib/format";

/** A rupee amount that glides from its previous value to the new one when it changes.
 *  On first render it shows the value as is: no count-up from zero. */
export function AnimatedRupees({ value }: { value: number }) {
  const mv = useMotionValue(value);
  const text = useTransform(mv, (v) => rupees(v));
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; mv.set(value); return; }
    const controls = animate(mv, value, { duration: 0.6, ease: [0.16, 1, 0.3, 1] });
    return () => controls.stop();
  }, [value, mv]);
  return <motion.span>{text}</motion.span>;
}
