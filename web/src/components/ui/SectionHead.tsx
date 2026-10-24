import { Pictogram, type PictogramName } from "./Pictogram";

/** A section title set like a wayfinding sign: a yellow pictogram tile, then the words. */
export function SectionHead({ id, icon, title, aside }: {
  id?: string; icon: PictogramName; title: string; aside?: React.ReactNode;
}) {
  return (
    <div className="section-head">
      <h2 id={id}>
        <span className="sign-tile"><Pictogram name={icon} size={20} /></span>
        {title}
      </h2>
      {aside && <div className="section-aside">{aside}</div>}
    </div>
  );
}
