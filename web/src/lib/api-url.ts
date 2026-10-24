// The API base URL, safe to import from client components (no server-only imports).
export const API_URL = (process.env.NEXT_PUBLIC_AEROPULSE_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
