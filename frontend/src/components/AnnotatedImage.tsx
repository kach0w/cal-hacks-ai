import { useIntersection } from "../hooks/useIntersection";
import { zoneToPercent } from "../lib/geometry";
import MarkerDetail from "./MarkerDetail";
import { useState } from "react";

/**
 * The HERO deliverable: numbered markers placed by NAMED ZONE over the real satellite
 * image. Placement is deterministic (lib/geometry) so a marker can't land on the wrong
 * corner. Each marker expands to its observation, corroboration, fix, and funding.
 */
export default function AnnotatedImage({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);
  const [open, setOpen] = useState<number | null>(null);

  if (loading) return <div className="rounded border p-6 text-sm">Loading analysis…</div>;
  if (!result) return <div className="rounded border p-6 text-sm">Not analyzed yet.</div>;

  return (
    <div className="space-y-3">
      <div className="relative inline-block">
        {result.annotated_image_url ? (
          <img src={result.annotated_image_url} alt="annotated intersection" className="rounded" />
        ) : (
          <div className="h-[400px] w-[400px] rounded bg-slate-100" />
        )}
        {result.findings.map((f, i) => {
          const pos = zoneToPercent(f.condition.zone);
          return (
            <button
              key={i}
              className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-600 px-2 text-xs text-white"
              style={{ left: pos.left, top: pos.top }}
              onClick={() => setOpen(open === i ? null : i)}
            >
              {i + 1}
            </button>
          );
        })}
      </div>
      {open !== null && <MarkerDetail finding={result.findings[open]} index={open + 1} />}
    </div>
  );
}
