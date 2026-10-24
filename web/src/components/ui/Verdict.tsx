import { LEVEL_CLASS, MARK, shortVerdict } from "@/lib/copy";
import type { Verdict } from "@/lib/types";

/** ▲ ▼ ● ○ in the level's colour. Always paired with words elsewhere. */
export function Mark({ v }: { v: Pick<Verdict, "level"> }) {
  return <span className={`mark ${LEVEL_CLASS[v.level]}`} aria-hidden="true">{MARK[v.level]}</span>;
}

/** "▲ 11% above usual" */
export function ShortVerdict({ v }: { v: Verdict }) {
  return (
    <span className={`${LEVEL_CLASS[v.level]} ${v.level === "above" ? "tone-up" : v.level === "below" ? "tone-down" : ""}`}>
      <Mark v={v} />{shortVerdict(v)}
    </span>
  );
}

/** The verdict as a filled chip: orange above usual, blue below, grey usual. */
export function VerdictChip({ v }: { v: Verdict }) {
  return <span className={`chip ${LEVEL_CLASS[v.level]}`}><Mark v={v} />{shortVerdict(v)}</span>;
}
