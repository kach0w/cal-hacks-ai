import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import type { ConceptRender } from "../types";

export default function BeforeAfterPanel({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);

  if (loading) {
    return (
      <section className="panel p-5">
        <div className="h-4 w-32 animate-pulse mb-4" style={{ background: "#d4d0c8" }} />
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-48 animate-pulse" style={{ background: "#d4d0c8" }} />
          ))}
        </div>
      </section>
    );
  }

  const renders = result?.renders ?? [];
  if (!renders.length) return null;

  return (
    <section className="panel overflow-hidden">
      <div className="px-5 py-4" style={{ borderBottom: "3px solid #2c3060" }}>
        <h2 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 10, color: "#1a1f3d" }}>▶ BEFORE / AFTER</h2>
        <p className="mt-1" style={{ fontFamily: '"VT323", monospace', fontSize: 17, color: "#6070a0" }}>
          Same POV — hazard removed by AI edit
        </p>
      </div>
      <div style={{ borderTop: "none" }}>
        {renders.map((r, i) => (
          <RenderRow key={i} render={r} index={i + 1} />
        ))}
      </div>
    </section>
  );
}

function RenderRow({ render, index }: { render: ConceptRender; index: number }) {
  const [tab, setTab] = useState<"before" | "after">("before");

  return (
    <div className="p-5" style={{ borderBottom: "2px solid #2c3060" }}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, background: "#e8c000", border: "2px solid #b89000", color: "#1a1f3d", padding: "3px 8px", display: "inline-block", marginBottom: 8 }}>
            #{index} · {render.zone}
          </span>
          <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#1a1f3d", lineHeight: 1.4 }}>{render.observation}</p>
          {render.fix && (
            <p style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", marginTop: 4 }}>Fix: {render.fix}</p>
          )}
        </div>
        <div className="flex shrink-0" style={{ border: "2px solid #2c3060", background: "#e8e4d4" }}>
          <button
            onClick={() => setTab("before")}
            style={{
              fontFamily: '"Press Start 2P", monospace',
              fontSize: 7,
              padding: "6px 10px",
              background: tab === "before" ? "#2c3060" : "transparent",
              color: tab === "before" ? "#e8c000" : "#6070a0",
              border: "none",
              cursor: "pointer",
            }}
          >
            BEFORE
          </button>
          <button
            onClick={() => setTab("after")}
            style={{
              fontFamily: '"Press Start 2P", monospace',
              fontSize: 7,
              padding: "6px 10px",
              background: tab === "after" ? "#2c3060" : "transparent",
              color: tab === "after" ? "#e8c000" : "#6070a0",
              border: "none",
              cursor: "pointer",
            }}
          >
            AFTER
          </button>
        </div>
      </div>

      <div style={{ border: "3px solid #2c3060", overflow: "hidden", background: "#1a1f3d" }}>
        {tab === "before" ? (
          render.before_url ? (
            <img src={render.before_url} alt={`Before — ${render.zone}`} className="h-56 w-full object-cover" />
          ) : (
            <div className="flex h-56 items-center justify-center" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#6070a0" }}>NO IMAGE</div>
          )
        ) : (
          render.after_url ? (
            <div className="relative">
              <img src={render.after_url} alt={`After — ${render.zone}`} className="h-56 w-full object-cover" />
              <span style={{ position: "absolute", bottom: 8, left: 8, fontFamily: '"Press Start 2P", monospace', fontSize: 6, background: "#0f1428", color: "#e8c000", border: "2px solid #e8c000", padding: "3px 6px" }}>
                {render.label}
              </span>
            </div>
          ) : (
            <div className="flex h-56 items-center justify-center" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#6070a0" }}>GENERATION FAILED</div>
          )
        )}
      </div>
    </div>
  );
}
