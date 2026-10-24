/** The aeronautical chart symbol for an airport: a ring with four ticks. Also our logo. */
export function AirportSymbol({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} aria-hidden="true" className={className}>
      <circle cx="10" cy="10" r="4.6" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M10 1.5v3.4M10 15.1v3.4M1.5 10h3.4M15.1 10h3.4" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
