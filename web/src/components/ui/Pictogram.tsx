// Airport-style pictograms, drawn on a 24-unit grid with bold strokes so they read at
// small sizes, the way wayfinding signs do.

const PATHS = {
  departures: (
    <>
      <path d="M2.5 19.5h19" />
      <path d="M4 15.2 20.2 9a1.9 1.9 0 0 0-1.3-3.6l-4.1 1.4L8.6 3.5l-2 .7 3.6 4.5-4.3 1.5-2-1.6-1.5.5 1.4 3.7" fill="currentColor" stroke="none" />
    </>
  ),
  arrivals: (
    <>
      <path d="M2.5 19.5h19" />
      <path d="m3.4 8.6 1.5-.5 2 1.8 4.4-.6-2.8-5 2.1-.3 4.8 4.6 4.3-.6a1.9 1.9 0 0 1 .5 3.8L3.9 14.1Z" fill="currentColor" stroke="none" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
      <path d="M3.5 10h17M8 3v4M16 3v4" />
      <path d="M7.5 13.5h2v2h-2zM11 13.5h2v2h-2zM14.5 13.5h2v2h-2z" fill="currentColor" stroke="none" />
    </>
  ),
  clock: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>),
  trend: (<><path d="M3 17.5 9 11.5l4 4 8-8.5" /><path d="M15 7h6v6" /></>),
  pin: (<><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Z" /><circle cx="12" cy="10" r="2.4" /></>),
  lamp: (
    <>
      <path d="M4 14.5c0 2.5 3.6 4.5 8 4.5s8-2 8-4.5Z" fill="currentColor" stroke="none" />
      <path d="M12 3.5c-1.6 2-2.3 3.4-2.3 4.7a2.3 2.3 0 0 0 4.6 0c0-1.3-.7-2.7-2.3-4.7Z" fill="currentColor" stroke="none" />
      <path d="M12 12v2" />
    </>
  ),
  compare: (<><path d="M4 18V9M10 18V5M16 18v-7M22 18H2" /></>),
  data: (<><ellipse cx="12" cy="6" rx="8" ry="2.8" /><path d="M4 6v12c0 1.5 3.6 2.8 8 2.8s8-1.3 8-2.8V6M4 12c0 1.5 3.6 2.8 8 2.8s8-1.3 8-2.8" /></>),
  info: (<><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5.5" /><circle cx="12" cy="7.8" r="0.6" fill="currentColor" /></>),
  route: (<><circle cx="5" cy="18" r="2.3" /><circle cx="19" cy="6" r="2.3" /><path d="M7 16.5C11 13 13 11 17 7.5" strokeDasharray="2.2 2.4" /></>),
  index: (<><path d="M3 20h18" /><path d="M3 15c3-4 5 1 8-3s5-6 10-6" /></>),
  week: (<><path d="M4 18h3v-5H4zM10.5 18h3V8h-3zM17 18h3v-8h-3z" fill="currentColor" stroke="none" /><path d="M2.5 20.5h19" /></>),
  check: (<><circle cx="12" cy="12" r="8.5" /><path d="m8 12.3 2.7 2.7L16.2 9.5" /></>),
  shield: (<><path d="M12 3 5 6v5.5c0 4.3 3 8 7 9.5 4-1.5 7-5.2 7-9.5V6Z" /><path d="m9 12 2.2 2.2L15.5 10" /></>),
  book: (<><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5Z" /><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5" /></>),
} as const;

export type PictogramName = keyof typeof PATHS;

export function Pictogram({ name, size = 20, className }: { name: PictogramName; size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden="true" className={className}
         fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {PATHS[name]}
    </svg>
  );
}
