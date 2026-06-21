import { useState } from "react";
import MapView from "./components/MapView";
import AgentFeed from "./components/AgentFeed";
import AnnotatedImage from "./components/AnnotatedImage";
import LastMilePanel from "./components/LastMilePanel";
import BeforeAfterPanel from "./components/BeforeAfterPanel";
import { ShieldPin, MapPin, Search } from "./components/icons";

export default function App() {
  const [selected, setSelected] = useState<{ lat: number; lng: number } | null>(null);

  if (!selected) return <MapView onSelect={setSelected} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-5 py-3.5">
          <button
            onClick={() => setSelected(null)}
            className="flex items-center gap-2.5 cursor-pointer"
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-amber-50 text-amber-500 ring-1 ring-amber-200">
              <ShieldPin className="h-5 w-5" />
            </span>
            <span className="hidden text-sm font-semibold tracking-tight text-gray-900 sm:block">
              Safe<span className="text-amber-500">Streets</span>
            </span>
          </button>

          <span className="hidden items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-500 md:inline-flex">
            <MapPin className="h-3.5 w-3.5 text-gray-400" />
            <span className="font-mono">{selected.lat.toFixed(4)}, {selected.lng.toFixed(4)}</span>
          </span>

          <button onClick={() => setSelected(null)} className="btn-ghost ml-auto px-3 py-2 text-xs">
            <Search className="h-4 w-4" />
            New search
          </button>
        </div>
      </header>

      <main
        key={`${selected.lat},${selected.lng}`}
        className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[minmax(0,1fr)_380px]"
      >
        <div className="min-w-0 space-y-5">
          <AnnotatedImage lat={selected.lat} lng={selected.lng} />
          <BeforeAfterPanel lat={selected.lat} lng={selected.lng} />
          <LastMilePanel lat={selected.lat} lng={selected.lng} />
        </div>
        <aside className="lg:sticky lg:top-[4.75rem] lg:h-[calc(100vh-6.5rem)]">
          <AgentFeed lat={selected.lat} lng={selected.lng} />
        </aside>
      </main>
    </div>
  );
}
