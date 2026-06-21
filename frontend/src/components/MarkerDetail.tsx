import type { Finding } from "../types";
import ConfidenceBadge from "./ConfidenceBadge";
import { Eye, Link, Sparkles, Banknote, Camera } from "./icons";



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
        <span className="grid h-8 w-8 place-items-center" style={{ background: "#e8c000", border: "2px solid #b89000", fontFamily: '"Press Start 2P", monospace', fontSize: 10, color: "#1a1f3d", fontWeight: "bold" }}>
          {index}
        </span>
        <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#1a1f3d", lineHeight: 1.6 }}>
          {iv?.name ?? c.observation}
        </h3>
        <ConfidenceBadge status={finding.status} />
        <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, border: "2px solid #2c3060", background: "#e8e4d4", padding: "3px 8px", color: "#6070a0" }}>
          {c.zone.replace("_", " ")}
        </span>
      </div>

      {/* Two independent signals */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="panel-quiet p-3.5">
          <p className="eyebrow flex items-center gap-1.5 mb-2" style={{ color: "#e8c000" }}>
            <Eye className="h-3 w-3" />
            SPOTTED — STREET SCAN
            <span className="ml-auto" style={{ color: "#6070a0" }}>{c.confidence}</span>
          </p>
          <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#1a1f3d", lineHeight: 1.4 }}>{c.observation}</p>
          <p className="mt-2 flex items-center gap-1.5" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0" }}>
            <Camera className="h-3 w-3" />
            {c.source_view}
            {c.source_capture_date ? ` · ${c.source_capture_date}` : ""}
          </p>
        </div>

        <div className="panel-quiet p-3.5">
          <p className="eyebrow flex items-center gap-1.5 mb-2" style={{ color: "#38a832" }}>
            <Link className="h-3 w-3" />
            CORROBORATION
          </p>
          {finding.corroboration.length > 0 ? (
            <ul className="space-y-2">
              {finding.corroboration.map((x, i) => (
                <li key={i} style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#1a1f3d", lineHeight: 1.4 }}>
                  <span style={{ fontWeight: "bold" }}>{x.source}</span>{" "}
                  <span style={{ color: "#3a3f60" }}>{x.reference}</span>
                  {x.excerpt && (
                    <span style={{ display: "block", borderLeft: "3px solid #2c3060", paddingLeft: 8, marginTop: 4, color: "#6070a0" }}>
                      {x.excerpt}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#6070a0" }}>
              No independent record matched — flagged for review.
            </p>
          )}
          {finding.crash_count_intersection != null && (
            <p className="mt-2" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0" }}>
              {finding.crash_count_intersection} crashes at intersection
            </p>
          )}
        </div>
      </div>

      {/* Candidate fix */}
      {iv && (
        <div className="p-4" style={{ border: "3px solid #e8c000", background: "rgba(232,192,0,0.08)" }}>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <p className="eyebrow flex items-center gap-1.5" style={{ color: "#e8c000" }}>
              <Sparkles className="h-3 w-3" />
              ▶ RECOMMENDED FIX
            </p>
            {cost && (
              <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, background: "#f0ece0", border: "2px solid #2c3060", padding: "4px 8px", color: "#1a1f3d" }}>
                {cost}
              </span>
            )}
          </div>
          <p style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#1a1f3d", marginBottom: 8 }}>{iv.name}</p>
          <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#3a3f60", lineHeight: 1.4 }}>{iv.evidence}</p>

          {iv.feasibility_caveat && (
            <p style={{ fontFamily: '"VT323", monospace', fontSize: 16, color: "#6070a0", marginTop: 8 }}>
              Feasibility: {iv.feasibility_caveat}
            </p>
          )}

          {iv.funding_program_keys.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Banknote className="h-4 w-4" style={{ color: "#38a832" }} />
              {iv.funding_program_keys.map((k) => (
                <span
                  key={k}
                  style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, border: "2px solid #38a832", background: "rgba(56,168,50,0.1)", padding: "3px 8px", color: "#38a832" }}
                >
                  {k}
                </span>
              ))}
            </div>
          )}

          {iv.disclaimer && (
            <p style={{ fontFamily: '"VT323", monospace', fontSize: 16, color: "#6070a0", marginTop: 10, borderTop: "2px solid #2c3060", paddingTop: 8, fontStyle: "italic" }}>
              {iv.disclaimer}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
