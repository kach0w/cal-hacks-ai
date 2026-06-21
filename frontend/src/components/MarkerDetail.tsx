import type { Finding } from "../types";
import ConfidenceBadge from "./ConfidenceBadge";
import { Eye, Link, Sparkles, Banknote, Camera } from "./icons";

const CONFIDENCE_TINT: Record<string, string> = {
  high: "text-confirmed",
  medium: "text-candidate",
  low: "text-slate-500",
};

function money(low: number | null, high: number | null, unit: string) {
  if (low == null && high == null) return null;
  const fmt = (n: number) =>
    n >= 1000 ? `$${(n / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 })}k` : `$${n}`;
  const range = low === high || high == null ? fmt(low!) : `${fmt(low!)}–${fmt(high!)}`;
  return `${range} · ${unit}`;
}

/** Click-to-expand: what was seen (+ confidence + imagery date), the independent
 *  corroboration, the candidate fix with its feasibility caveat, cost, and funding. */
export default function MarkerDetail({ finding, index }: { finding: Finding; index: number }) {
  const c = finding.condition;
  const iv = finding.intervention;
  const cost = iv ? money(iv.cost_low, iv.cost_high, iv.cost_unit) : null;

  return (
    <div className="animate-fade-up space-y-4">
      <div className="flex flex-wrap items-center gap-2.5">
        <span className="grid h-7 w-7 place-items-center rounded-full bg-white/[0.06] font-mono text-sm font-bold text-white">
          {index}
        </span>
        <h3 className="text-base font-semibold text-white">
          {iv?.name ?? c.observation}
        </h3>
        <ConfidenceBadge status={finding.status} />
        <span className="rounded-md bg-white/[0.05] px-2 py-0.5 font-mono text-[11px] text-slate-400">
          {c.zone.replace("_", " ")}
        </span>
      </div>

      {/* Two independent signals */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="panel-quiet p-3.5">
          <p className="eyebrow flex items-center gap-1.5 text-brand">
            <Eye className="h-3.5 w-3.5" />
            Seen — blind pass
            <span className={`ml-auto font-mono ${CONFIDENCE_TINT[c.confidence] ?? ""}`}>
              {c.confidence}
            </span>
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-300">{c.observation}</p>
          <p className="mt-2 flex items-center gap-1.5 font-mono text-[11px] text-slate-500">
            <Camera className="h-3 w-3" />
            {c.source_view}
            {c.source_capture_date ? ` · ${c.source_capture_date}` : ""}
            {c.not_visually_confirmable && " · not visually confirmable"}
          </p>
        </div>

        <div className="panel-quiet p-3.5">
          <p className="eyebrow flex items-center gap-1.5 text-confirmed">
            <Link className="h-3.5 w-3.5" />
            Corroborated — independent
          </p>
          {finding.corroboration.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {finding.corroboration.map((x, i) => (
                <li key={i} className="text-sm leading-relaxed text-slate-300">
                  <span className="font-medium text-white">{x.source}</span>{" "}
                  <span className="text-slate-400">{x.reference}</span>
                  {x.excerpt && (
                    <span className="mt-0.5 block border-l-2 border-white/10 pl-2 text-slate-400">
                      {x.excerpt}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-slate-500">
              No independent record matched yet — flagged as a candidate.
            </p>
          )}
          {finding.crash_count_intersection != null && (
            <p className="mt-2 font-mono text-[11px] text-slate-500">
              {finding.crash_count_intersection} crashes at intersection · attribution shown at
              source precision
            </p>
          )}
        </div>
      </div>

      {/* Candidate fix */}
      {iv && (
        <div className="rounded-xl border border-brand/20 bg-brand/[0.06] p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-brand-soft">
              <Sparkles className="h-4 w-4" />
              Candidate fix
            </p>
            {cost && (
              <span className="rounded-md bg-ink-950/40 px-2 py-1 font-mono text-xs text-white">
                {cost}
              </span>
            )}
          </div>
          <p className="mt-2 text-sm font-medium text-white">{iv.name}</p>
          <p className="mt-1 text-sm leading-relaxed text-slate-300">{iv.evidence}</p>

          {iv.feasibility_caveat && (
            <p className="mt-2.5 text-xs leading-relaxed text-slate-400">
              <span className="font-semibold text-slate-300">Feasibility:</span>{" "}
              {iv.feasibility_caveat}
            </p>
          )}

          {iv.funding_program_keys.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Banknote className="h-4 w-4 text-confirmed" />
              {iv.funding_program_keys.map((k) => (
                <span
                  key={k}
                  className="rounded-md border border-confirmed/25 bg-confirmed/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-confirmed"
                >
                  {k}
                </span>
              ))}
            </div>
          )}

          {iv.disclaimer && (
            <p className="mt-3 border-t border-white/10 pt-2.5 text-[11px] italic leading-relaxed text-slate-500">
              {iv.disclaimer}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
