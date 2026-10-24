// Every sentence the site generates from data, in one place.
// Voice: plain words, sentence case, active. Describe what fares have done; never predict.
import type { Level, Verdict } from "./types";
import { pct, rupees } from "./format";

export const MIN_HISTORY = 21;

export const MARK: Record<Level, string> = { above: "▲", below: "▼", typical: "●", unknown: "○" };

export const LEVEL_CLASS: Record<Level, string> = {
  above: "lv-up", below: "lv-down", typical: "lv-usual", unknown: "lv-unknown",
};

const WINDOW_PHRASE: Record<string, string> = {
  "1-7": "within a week", "8-14": "1–2 weeks out", "15-30": "2–4 weeks out",
  "31-60": "1–2 months out",
};
export const windowPhrase = (key: string) => WINDOW_PHRASE[key] ?? key;

/** The direct answer to "is my fare high?" */
export function answer(v: Verdict): string {
  return {
    above: "Yes, higher than usual.",
    below: "No, lower than usual.",
    typical: "No, about usual.",
    unknown: "Too early to say.",
  }[v.level];
}

/** One sentence under the answer, in words; the numbers sit in the strip below it. */
export function context(v: Verdict, window: string, from: string, to: string): string {
  if (v.level === "unknown") {
    const need = Math.max(MIN_HISTORY - v.history_days, 0);
    return `We need ${MIN_HISTORY} days of prices before we can say what is usual for ${from} to ${to}. ${need} more to go.`;
  }
  const lead = `Cheapest fares from ${from} to ${to}, flying ${windowPhrase(window)},`;
  if (v.level === "typical") return `${lead} sit inside the range that has been usual for the last 90 days.`;
  const word = v.level === "above" ? "above" : "below";
  return `${lead} are ${pct(v.pct_vs_usual)} ${word} what has been usual for the last 90 days.`;
}

/** For lists: "11% above usual", "Usual", "Too new to judge" */
export function shortVerdict(v: Verdict): string {
  if (v.level === "unknown") return "Too new to judge";
  if (v.level === "typical") return "Usual";
  return `${pct(v.pct_vs_usual)} ${v.level === "above" ? "above" : "below"} usual`;
}

export function indexVerdict(v: Verdict, subject = "Domestic fares"): string {
  if (v.level === "unknown") return `${subject}: not enough history yet to say what is usual.`;
  if (v.level === "typical") return `${subject} are about where they usually are.`;
  return `${subject} are ${pct(v.pct_vs_usual)} ${v.level === "above" ? "above" : "below"} usual.`;
}

export function usualRange(v: Verdict): string {
  if (v.usual_low == null || v.usual_high == null) return "Building up";
  return `${rupees(v.usual_low)}–${rupees(v.usual_high).slice(1)}`;
}

/** "Over the last month, fares were usually lowest 6 to 9 weeks before departure." */
export function cheapestSentence(stretch: [number, number] | null): string {
  if (!stretch) return "Not enough data yet to say when this route is usually cheapest.";
  const [a, b] = stretch;
  let span: string;
  if (a >= 14) {
    const lo = Math.round(a / 7), hi = Math.round(b / 7);
    span = lo === hi ? `about ${lo} weeks` : `${lo} to ${hi} weeks`;
  } else {
    span = a === b ? `about ${a} days` : `${a} to ${b} days`;
  }
  return `Over the last month, fares were usually lowest ${span} before departure.`;
}

export const WEEKDAY_NAMES: Record<string, string> = {
  Mon: "Monday", Tue: "Tuesday", Wed: "Wednesday", Thu: "Thursday", Fri: "Friday",
  Sat: "Saturday", Sun: "Sunday",
};
