import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import type { ConceptRender } from "../types";

export default function BeforeAfterPanel({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);

  if (loading) {
    return (
      <section className="panel p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Before / After</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      </section>
    );
  }

  const renders = result?.renders ?? [];
  if (!renders.length) return null;

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-gray-100 px-5 py-4">
        <h2 className="text-[15px] font-semibold text-gray-900">Before / After</h2>
        <p className="mt-0.5 text-xs text-gray-400">
          AI-generated concept illustrations — not photos of this site
        </p>
      </div>
      <div className="divide-y divide-gray-100">
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
    <div className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700 ring-1 ring-amber-200">
            {render.zone}
          </span>
          <p className="mt-1.5 text-sm text-gray-700">{render.observation}</p>
          {render.fix && (
            <p className="mt-0.5 text-xs text-gray-400">Fix: {render.fix}</p>
          )}
        </div>
        <div className="flex shrink-0 rounded-lg border border-gray-200 bg-gray-50 p-0.5 text-xs font-medium">
          <button
            onClick={() => setTab("before")}
            className={`rounded-md px-3 py-1.5 transition-colors ${tab === "before" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            Before
          </button>
          <button
            onClick={() => setTab("after")}
            className={`rounded-md px-3 py-1.5 transition-colors ${tab === "after" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            After
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-gray-100">
        {tab === "before" ? (
          render.before_url ? (
            <img src={render.before_url} alt={`Before — ${render.zone}`} className="h-56 w-full object-cover" />
          ) : (
            <div className="flex h-56 items-center justify-center text-sm text-gray-400">No image</div>
          )
        ) : (
          render.after_url ? (
            <div className="relative">
              <img src={render.after_url} alt={`After — ${render.zone}`} className="h-56 w-full object-cover" />
              <span className="absolute bottom-2 left-2 rounded bg-black/60 px-2 py-1 text-[10px] text-white">
                {render.label}
              </span>
            </div>
          ) : (
            <div className="flex h-56 items-center justify-center text-sm text-gray-400">Generation failed</div>
          )
        )}
      </div>
    </div>
  );
}
