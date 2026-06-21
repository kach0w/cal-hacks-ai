import { useState } from "react";
import MapView from "./components/MapView";
import AgentFeed from "./components/AgentFeed";
import AnnotatedImage from "./components/AnnotatedImage";
import LastMilePanel from "./components/LastMilePanel";
import ResidentSubmit from "./components/ResidentSubmit";
import { ShieldPin, MapPin, Search } from "./components/icons";

/**
 * Top-level flow:
 *  1. user picks an intersection on the map / search (MapView)
 *  2. AgentFeed streams the pipeline (blind vision -> corroboration -> accountability)
 *  3. AnnotatedImage shows markers on the real image; LastMilePanel shows the actions
 */
export default function App() {
  const [selected, setSelected] = useState<{ lat: number; lng: number } | null>(null);

  if (!selected) return <MapView onSelect={setSelected} />;

  return (
    <div className="min-h-screen">
      {/* Sticky workspace header */}
      <header className="sticky top-0 z-30 border-b border-white/10 bg-ink-950/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-5 py-3.5">
          <button
            onClick={() => setSelected(null)}
            className="flex items-center gap-2.5 cursor-pointer"
            aria-label="Back to search"
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand/15 text-brand ring-1 ring-brand/30">
              <ShieldPin className="h-5 w-5" />
            </span>
            <span className="hidden text-sm font-semibold tracking-tight text-white sm:block">
              Safe<span className="text-brand">Streets</span>
            </span>
          </button>

          <span className="hidden items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 md:inline-flex">
            <MapPin className="h-3.5 w-3.5 text-slate-500" />
            <span className="font-mono">
              {selected.lat.toFixed(4)}, {selected.lng.toFixed(4)}
            </span>
          </span>

          <button onClick={() => setSelected(null)} className="btn-ghost ml-auto px-3 py-2 text-xs">
            <Search className="h-4 w-4" />
            New search
          </button>
        </div>
      </header>

      {/* Workspace — remount per intersection so streams reset */}
      <main
        key={`${selected.lat},${selected.lng}`}
        className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[minmax(0,1fr)_380px]"
      >
        <div className="min-w-0 space-y-5">
          <AnnotatedImage lat={selected.lat} lng={selected.lng} />
          <LastMilePanel lat={selected.lat} lng={selected.lng} />
          <ResidentSubmit lat={selected.lat} lng={selected.lng} />
        </div>

        <aside className="lg:sticky lg:top-[4.75rem] lg:h-[calc(100vh-6.5rem)]">
          <AgentFeed lat={selected.lat} lng={selected.lng} />
        </aside>
      </main>
    </div>
  );
}
