import { Pictogram, type PictogramName } from "./Pictogram";

/** The dark sign band that opens every inner page, with a large pictogram on the right. */
export function PageHead({ icon, title, lede, crumbs, children }: {
  icon: PictogramName; title: React.ReactNode; lede?: React.ReactNode; crumbs?: React.ReactNode; children?: React.ReactNode;
}) {
  return (
    <div className="sign sign-band page-head-band">
      <div className="wrap page-head">
        {crumbs && <p className="crumbs">{crumbs}</p>}
        <h1>{title}</h1>
        {lede && <p className="lede">{lede}</p>}
        {children}
      </div>
      <Pictogram name={icon} size={180} className="head-icon" />
    </div>
  );
}
