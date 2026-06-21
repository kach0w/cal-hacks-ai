import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import { zoneToPercent } from "../lib/geometry";
import MarkerDetail from "./MarkerDetail";
import ConceptToggle from "./ConceptToggle";
import type { FindingStatus } from "../types";
import { MapPin, Camera, Eye } from "./icons";

/**
 * The HERO deliverable: numbered markers placed by NAMED ZONE over the real satellite
 * image. Placement is deterministic (lib/geometry) so a marker can't land on the wrong
 * corner. Each marker expands to its observation, corroboration, fix, and funding.
 */

const MARKER: Record<FindingStatus, string> = {
  CONFIRMED: "bg-green-500 text-white ring-green-300",
  CANDIDATE: "bg-amber-400 text-white ring-amber-200",
  REPORTED: "bg-amber-400 text-white ring-amber-200",
};
const RING: Record<FindingStatus, string> = {
  CONFIRMED: "bg-green-400/40",
  CANDIDATE: "bg-amber-400/40",
  REPORTED: "bg-amber-400/40",
};

const LABEL: Record<FindingStatus, string> = {
  CONFIRMED: "Confirmed",
  CANDIDATE: "Problem",
  REPORTED: "Problem",
};

const CORNERS = [
  { label: "NW", pos: "left-3 top-3" },
  { label: "NE", pos: "right-3 top-3" },
  { label: "SW", pos: "left-3 bottom-3" },
  { label: "SE", pos: "right-3 bottom-3" },
];

export default function AnnotatedImage({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);
  const [open, setOpen] = useState<number | null>(null);

  const captureDate =
    result?.findings.find((f) => f.condition.source_capture_date)?.condition.source_capture_date ??
    null;

  return (
    <section className="panel overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4" style={{ borderBottom: "3px solid #2c3060" }}>
        <div>
          <p className="eyebrow flex items-center gap-1.5">
            <Eye className="h-3 w-3" style={{ color: "#e8c000" }} />
            ▶ STREET ANALYSIS RESULT
          </p>
          <h2 className="mt-2 flex items-center gap-2" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#1a1f3d" }}>
            <MapPin className="h-4 w-4" style={{ color: "#6070a0" }} />
            {result?.intersection.address ?? `${lat.toFixed(4)}, ${lng.toFixed(4)}`}
          </h2>
        </div>
        {captureDate && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5" style={{ border: "2px solid #2c3060", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0" }}>
            <Camera className="h-3 w-3" />
            {captureDate}
          </span>
        )}
      </div>

      {/* Image stage */}
      <div className="p-5">
        <div className="relative mx-auto aspect-square w-full max-w-[560px] overflow-hidden rounded-xl border border-gray-200 bg-white">
          {/* Real image, or a canonical-frame placeholder */}
          {result?.annotated_image_url ? (
            <img
              src={result.annotated_image_url}
              alt={`Annotated satellite view of ${result.intersection.address}`}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 bg-grid-faint [background-size:32px_32px]">
              {/* Canonical intersection frame: the two legs */}
              <div className="absolute left-1/2 top-0 h-full w-16 -translate-x-1/2 bg-gray-50" />
              <div className="absolute top-1/2 left-0 h-16 w-full -translate-y-1/2 bg-gray-50" />
              {loading && (
                <div className="absolute inset-x-0 top-0 h-24 animate-scan bg-gradient-to-b from-brand/20 to-transparent" />
              )}
            </div>
          )}

          {/* Faint corner zone labels (the canonical frame) */}
          {CORNERS.map((c) => (
            <span
              key={c.label}
              className={`absolute ${c.pos} rounded-md bg-white px-1.5 py-0.5 font-mono text-[10px] tracking-widest text-gray-500 backdrop-blur-sm`}
            >
              {c.label}
            </span>
          ))}

          {/* Markers */}
          {result?.findings.map((f, i) => {
            const pos = zoneToPercent(f.condition.zone);
            const active = open === i;
            return (
              <button
                key={i}
                aria-label={`Finding ${i + 1}: ${f.status} at ${f.condition.zone}`}
                className="group absolute z-10 cursor-pointer"
                style={{ left: pos.left, top: pos.top, transform: "translate(-50%,-50%)" }}
                onClick={() => setOpen(active ? null : i)}
              >
                <span
                  className={`absolute left-1/2 top-1/2 h-9 w-9 rounded-full ${RING[f.status]} animate-ping-ring`}
                />
                <span
                  className={`relative grid h-8 w-8 place-items-center rounded-full font-mono text-sm font-bold shadow-marker ring-2 transition-transform duration-200 group-hover:scale-110 ${
                    MARKER[f.status]
                  } ${active ? "scale-110 ring-4" : ""}`}
                  style={{ animation: `marker-in 0.5s ${i * 120}ms both` }}
                >
                  {i + 1}
                </span>
              </button>
            );
          })}

          {loading && !result && (
            <div className="absolute inset-0 grid place-items-center">
              <p className="rounded-lg bg-white px-3 py-1.5 font-mono text-xs text-gray-500 backdrop-blur">
                fetching satellite + Street View…
              </p>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <Legend color="bg-green-500" label="CORROBORATED" />
          <Legend color="bg-yellow-400" label="NOT CORROBORATED" />
        </div>
      </div>

      {/* Selected finding detail */}
      {open !== null && result && (
        <div className="p-5" style={{ borderTop: "3px solid #2c3060" }}>
          <MarkerDetail finding={result.findings[open]} index={open + 1} />
        </div>
      )}

      {/* Concept illustration (clearly labeled, secondary) */}
      {result?.concept_image_url && (
        <div className="border-t border-gray-200 p-5">
          <ConceptToggle conceptUrl={result.concept_image_url} />
        </div>
      )}
    </section>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#3a3f60" }}>
      <span className={`h-3 w-3 ${color}`} style={{ display: "inline-block" }} />
      {label}
    </span>
  );
}
