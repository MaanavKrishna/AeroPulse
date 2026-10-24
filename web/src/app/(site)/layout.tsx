import { Suspense } from "react";

import { CommandPalette } from "@/components/site/CommandPalette";
import { DemoNotice } from "@/components/site/DemoNotice";
import { Footer } from "@/components/site/Footer";
import { Header } from "@/components/site/Header";
import { getAirports, getRoutes } from "@/lib/api";

async function Palette() {
  const [routes, airports] = await Promise.all([getRoutes(), getAirports()]);
  return <CommandPalette routes={routes} airports={airports} />;
}

/** The site chrome: notice, header, footer and the ⌘K search. Embeds live outside it. */
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <Suspense fallback={null}><DemoNotice /></Suspense>
      <Header />
      <main id="main">{children}</main>
      <Footer />
      <Suspense fallback={null}><Palette /></Suspense>
    </>
  );
}
