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
    <div className="min-h-screen" style={{ background: "#1a1f3d" }}>
      <header className="sticky top-0 z-30" style={{ background: "#0f1428", borderBottom: "4px solid #2c3060" }}>
        <div className="mx-auto flex max-w-4xl items-center gap-4 px-5 py-3">
          <button onClick={() => setSelected(null)} className="flex items-center gap-3 cursor-pointer">
            <span className="grid h-8 w-8 place-items-center" style={{ background: "#e8c000", border: "2px solid #b89000" }}>
              <ShieldPin className="h-4 w-4" style={{ color: "#1a1f3d" }} />
            </span>
            <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 10, color: "#f0ece0", letterSpacing: "0.05em" }}>
              STREETS OF <span style={{ color: "#e8c000" }}>BERKELEY</span>
            </span>
          </button>

          <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1" style={{ border: "2px solid #2c3060", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0" }}>
            <MapPin className="h-3 w-3" />
            {selected.lat.toFixed(4)}, {selected.lng.toFixed(4)}
          </span>

          <button onClick={() => setSelected(null)} className="btn-ghost ml-auto" style={{ fontSize: 8, padding: "8px 12px" }}>
            <Search className="h-3 w-3" />
            NEW SEARCH
          </button>
        </div>
      </header>

      <main
        key={`${selected.lat},${selected.lng}`}
        className="mx-auto max-w-4xl space-y-5 px-5 py-6"
      >
        <AnnotatedImage lat={selected.lat} lng={selected.lng} />
        <BeforeAfterPanel lat={selected.lat} lng={selected.lng} />
        <LastMilePanel lat={selected.lat} lng={selected.lng} />
      </main>
    </div>
  );
}
