import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import { zoneToPercent } from "../lib/geometry";
import MarkerDetail from "./MarkerDetail";
import ConceptToggle from "./ConceptToggle";
import { MapPin, Camera, Eye } from "./icons";

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
                aria-label={`Finding ${i + 1} at ${f.condition.zone}`}
                className="group absolute z-10 cursor-pointer"
                style={{ left: pos.left, top: pos.top, transform: "translate(-50%,-50%)" }}
                onClick={() => setOpen(active ? null : i)}
              >
                <span
                  className="relative grid h-8 w-8 place-items-center font-mono text-sm font-bold group-hover:scale-110 transition-transform duration-150"
                  style={{
                    background: "#e84040",
                    border: active ? "3px solid #fff" : "3px solid #8b0000",
                    boxShadow: active ? "0 0 0 2px #e84040" : "3px 3px 0 #8b0000",
                    color: "#fff",
                    fontFamily: '"Press Start 2P", monospace',
                    fontSize: 10,
                    animation: `marker-in 0.5s ${i * 120}ms both`,
                  }}
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
