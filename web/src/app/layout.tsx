import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";

import { MotionProvider } from "@/components/site/MotionProvider";
import { SITE_URL } from "@/lib/site";

import "@/styles/tokens.css";
import "@/styles/base.css";

const anek = localFont({
  src: [
    { path: "./fonts/anek-latin-latin-wdth-normal.woff2", weight: "100 800", style: "normal" },
    { path: "./fonts/anek-latin-latin-ext-wdth-normal.woff2", weight: "100 800", style: "normal" },
  ],
  variable: "--font-anek",
  display: "swap",
  declarations: [{ prop: "font-stretch", value: "75% 125%" }],
});

const serif = localFont({
  src: [
    { path: "./fonts/source-serif-4-latin-wght-normal.woff2", weight: "200 900", style: "normal" },
    { path: "./fonts/source-serif-4-latin-wght-italic.woff2", weight: "200 900", style: "italic" },
  ],
  variable: "--font-serif",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "AeroPulse: is your flight fare high today?", template: "%s | AeroPulse" },
  description:
    "See whether domestic flight fares in India are higher or lower than usual, route by route. Open data, open method, no predictions.",
  openGraph: { siteName: "AeroPulse", type: "website", locale: "en_IN" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f2f5f7" },
    { media: "(prefers-color-scheme: dark)", color: "#0d1520" },
  ],
};

// Applies the saved theme before first paint, so there is no flash of the wrong one.
const themeScript = `try{var t=localStorage.getItem("aeropulse-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-IN" className={`${anek.variable} ${serif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}
