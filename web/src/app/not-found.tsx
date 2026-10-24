import Link from "next/link";

import { Pictogram } from "@/components/ui/Pictogram";

export default function NotFound() {
  return (
    <main className="sign sign-band page-head-band" style={{ minHeight: "100vh", display: "grid", alignContent: "center" }}>
      <div className="wrap page-head">
        <p className="crumbs">Error 404</p>
        <h1>This gate doesn&apos;t exist</h1>
        <p className="lede">
          The page you asked for isn&apos;t here. If you typed a route, use airport codes with a dash, like DEL-BOM.
        </p>
        <p style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "1.5rem" }}>
          <Link className="btn btn-primary" href="/">Go to the home page</Link>
          <Link className="btn btn-quiet" href="/routes">See all routes</Link>
        </p>
      </div>
      <Pictogram name="departures" size={180} className="head-icon" />
    </main>
  );
}
