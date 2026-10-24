import type { Metadata } from "next";
import { Suspense } from "react";

import { FestivalBoard } from "@/components/ui/FestivalBoard";
import { PageHead } from "@/components/ui/PageHead";
import { getFestivals, getMeta } from "@/lib/api";

export const metadata: Metadata = {
  title: "Festival airfares in India",
  description: "How far above ordinary weeks domestic fares are for Diwali, Chhath, Christmas and Holi travel, route by route.",
};

async function Board() {
  const [festivals, meta] = await Promise.all([getFestivals(), getMeta()]);
  return (
    <>
      <FestivalBoard festivals={festivals} today={meta.latest_date ?? festivals[0].date} />
      <p className="small muted mt-4">Lunar festival dates can move by a day between calendars. Dates we have not confirmed against
        the official holiday list are shown as &ldquo;around&rdquo;. Routes are an editorial choice of where festival travel is heaviest.</p>
    </>
  );
}

export default function FestivalsPage() {
  return (
    <>
      <PageHead icon="lamp" title="Festival fares"
                lede="For each festival we follow the cheapest fare for the busiest travel day, two days before, and compare it with ordinary dates booked the same distance ahead." />
      <div className="wrap page-body">
        <Suspense fallback={<p className="muted">Loading…</p>}><Board /></Suspense>
      </div>
    </>
  );
}
