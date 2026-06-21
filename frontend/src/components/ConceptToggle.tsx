import { useState } from "react";
import { Sparkles, Eye, EyeOff } from "./icons";

/**
 * Optional, SECONDARY Midjourney concept illustration. ALWAYS rendered with the
 * 'Illustrative concept - not a photo of this site' label, behind a toggle. The honest
 * primary 'after' is the overlay on the real photo, not this.
 */
export default function ConceptToggle({ conceptUrl }: { conceptUrl: string | null }) {
  const [show, setShow] = useState(false);
  if (!conceptUrl) return null;

  return (
    <div>
      <div className="flex items-center justify-between">
        <p className="eyebrow flex items-center gap-1.5 text-candidate">
          <Sparkles className="h-3.5 w-3.5" />
          Concept illustration
        </p>
        <button
          onClick={() => setShow((s) => !s)}
          className="btn-ghost px-3 py-1.5 text-xs"
          aria-expanded={show}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          {show ? "Hide" : "Show concept"}
        </button>
      </div>

      {show && (
        <figure className="mt-3 animate-fade-up">
          <div className="relative overflow-hidden rounded-xl border border-candidate/20">
            <img src={conceptUrl} alt="Illustrative concept of the proposed fix" className="w-full" />
            <span className="absolute left-3 top-3 rounded-md bg-ink-950/75 px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-widest text-candidate backdrop-blur">
              Illustrative concept
            </span>
          </div>
          <figcaption className="mt-2 text-xs text-slate-500">
            Illustrative concept — not a photo of this site. The honest "after" is the annotated
            overlay on the real image above.
          </figcaption>
        </figure>
      )}
    </div>
  );
}
