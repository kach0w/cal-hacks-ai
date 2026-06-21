import { Download } from "./icons";

/**
 * Exports a structured one-pager for a council meeting: the annotated real image, the
 * top 3 fixes with costs and citations, the funding match, the named messenger, and the
 * accountability record. Structured data into a template — NOT AI-generated prose.
 * TODO: render to printable HTML / PDF.
 */
export default function OnePagerExport() {
  return (
    <button className="btn-primary py-2 text-xs" onClick={() => window.print()}>
      <Download className="h-4 w-4" />
      Export for council meeting
    </button>
  );
}
