import { useState } from "react";
import { submitReport } from "../api/client";
import { Camera, Users, Check } from "./icons";

/** Resident submission: a current photo + description that fills data deserts, supersedes
 *  stale Street View, and counts toward the corridor coalition. */
export default function ResidentSubmit({ lat, lng }: { lat: number; lng: number }) {
  const [desc, setDesc] = useState("");
  const [count, setCount] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!desc.trim() || busy) return;
    setBusy(true);
    try {
      const r = await submitReport({ lat, lng, description: desc });
      setCount(r.coalition_count);
      setDesc("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel p-5">
      <p className="eyebrow flex items-center gap-1.5 text-brand">
        <Camera className="h-3.5 w-3.5" />
        Resident report
      </p>
      <h2 className="mt-1 text-[15px] font-semibold text-white">Seen something the map missed?</h2>
      <p className="mt-1 text-sm leading-relaxed text-slate-400">
        A current photo supersedes stale Street View and adds your voice to the corridor coalition.
      </p>

      <div className="mt-4 space-y-3">
        <label htmlFor="resident-desc" className="sr-only">
          What's wrong at this intersection?
        </label>
        <textarea
          id="resident-desc"
          rows={3}
          className="w-full resize-none rounded-xl border border-white/10 bg-ink-900/60 p-3 text-sm text-white placeholder:text-slate-500 transition-colors focus:border-brand/50"
          placeholder="e.g. the shrubs on the SE corner block the view of the crossing…"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-ghost px-3 py-2 text-xs"
            title="Photo upload coming soon"
          >
            <Camera className="h-4 w-4" />
            Attach photo
          </button>
          <button
            type="button"
            className="btn-primary ml-auto"
            onClick={send}
            disabled={busy || !desc.trim()}
          >
            {busy ? "Submitting…" : "Submit report"}
          </button>
        </div>

        {count !== null && (
          <p className="flex items-center gap-2 rounded-lg border border-confirmed/25 bg-confirmed/10 px-3 py-2 text-sm text-confirmed animate-fade-up">
            <Check className="h-4 w-4 shrink-0" />
            <span className="inline-flex items-center gap-1.5">
              <Users className="h-4 w-4" />
              {count} residents have now flagged this corridor.
            </span>
          </p>
        )}
      </div>
    </section>
  );
}
