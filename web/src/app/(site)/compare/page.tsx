import type { Metadata } from "next";
import { Suspense } from "react";

import { CompareTool } from "@/components/compare/CompareTool";
import { PageHead } from "@/components/ui/PageHead";
import { getRoutes } from "@/lib/api";

export const metadata: Metadata = {
  title: "Compare routes",
  description: "Put up to four routes on one chart and see how their fares moved against each other.",
};

async function Compare() {
  const routes = await getRoutes();
  return <CompareTool routes={routes} initial={["DEL-BOM", "BOM-DEL", "DEL-BLR"]} />;
}

export default function ComparePage() {
  return (
    <>
      <PageHead icon="compare" title="Compare routes"
                lede="Up to four routes on one chart. Each line is that route's index, rebased so they all start at 100, so you compare movement, not price levels." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Loading routes…</p>}><Compare /></Suspense>
      </div>
    </>
  );
}
