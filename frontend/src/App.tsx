import { useState } from "react";
import MapView from "./components/MapView";
import AnnotatedImage from "./components/AnnotatedImage";
import LastMilePanel from "./components/LastMilePanel";
import BeforeAfterPanel from "./components/BeforeAfterPanel";
import { ShieldPin, MapPin, Search } from "./components/icons";

export default function App() {
  const [selected, setSelected] = useState<{ lat: number; lng: number } | null>(null);

  if (!selected) return <MapView onSelect={setSelected} />;

  return (
    <div className="min-h-screen" style={{ background: "#f5f4ef" }}>
      <header className="sticky top-0 z-30 border-b border-[#d4d0c8] bg-white">
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-5 py-3">
          <button
            onClick={() => setSelected(null)}
            className="flex items-center gap-2 cursor-pointer"
          >
            <span className="grid h-7 w-7 place-items-center bg-amber-100 text-amber-600" style={{ borderRadius: 2 }}>
              <ShieldPin className="h-4 w-4" />
            </span>
            <span className="text-base font-bold tracking-tight text-gray-900">
              Safe<span className="text-amber-600">Streets</span>
            </span>
          </button>

          <span className="hidden items-center gap-1.5 border border-[#d4d0c8] bg-[#faf9f6] px-2.5 py-1 text-xs text-gray-500 md:inline-flex font-mono" style={{ borderRadius: 2 }}>
            <MapPin className="h-3 w-3 text-gray-400" />
            {selected.lat.toFixed(4)}, {selected.lng.toFixed(4)}
          </span>

          <button onClick={() => setSelected(null)} className="btn-ghost ml-auto px-3 py-1.5 text-xs">
            <Search className="h-3.5 w-3.5" />
            New search
          </button>
        </div>
      </header>

      <main
        key={`${selected.lat},${selected.lng}`}
        className="mx-auto max-w-4xl space-y-4 px-5 py-5"
      >
        <AnnotatedImage lat={selected.lat} lng={selected.lng} />
        <BeforeAfterPanel lat={selected.lat} lng={selected.lng} />
        <LastMilePanel lat={selected.lat} lng={selected.lng} />
      </main>
    </div>
  );
}
