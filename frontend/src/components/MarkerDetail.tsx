import type { Finding } from "../types";
import ConfidenceBadge from "./ConfidenceBadge";

/** Click-to-expand: what was seen (+ confidence + imagery date), the independent
 *  corroboration, the candidate fix with its feasibility caveat, cost, and funding. */
export default function MarkerDetail({ finding, index }: { finding: Finding; index: number }) {
  const c = finding.condition;
  const iv = finding.intervention;
  return (
    <div className="rounded border p-4 text-sm space-y-2">
      <div className="flex items-center gap-2">
        <span className="font-semibold">[{index}] {c.zone}</span>
        <ConfidenceBadge status={finding.status} />
      </div>
      <p><span className="text-slate-500">Seen ({c.confidence}):</span> {c.observation}
        {c.source_capture_date && <em className="text-slate-400"> · imagery {c.source_capture_date}</em>}</p>
      {finding.corroboration.length > 0 && (
        <p><span className="text-slate-500">Corroborated:</span>{" "}
          {finding.corroboration.map((x) => `${x.source} ${x.reference}`).join("; ")}</p>
      )}
      {iv && (
        <div className="rounded bg-slate-50 p-2">
          <p className="font-medium">{iv.name}</p>
          {iv.feasibility_caveat && <p className="text-xs text-slate-500">Feasibility: {iv.feasibility_caveat}</p>}
          <p className="text-xs text-slate-400">{iv.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
