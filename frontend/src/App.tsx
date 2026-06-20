import { useState } from "react";
import MapView from "./components/MapView";
import AgentFeed from "./components/AgentFeed";
import AnnotatedImage from "./components/AnnotatedImage";
import LastMilePanel from "./components/LastMilePanel";

/**
 * Top-level flow:
 *  1. user picks an intersection on the map
 *  2. AgentFeed streams the pipeline (blind vision -> corroboration -> accountability)
 *  3. AnnotatedImage shows markers on the real image; LastMilePanel shows the actions
 */
export default function App() {
  const [selected, setSelected] = useState<{ lat: number; lng: number } | null>(null);

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[1fr_400px]">
      <main className="p-4 space-y-4">
        {!selected ? (
          <MapView onSelect={setSelected} />
        ) : (
          <>
            <AnnotatedImage lat={selected.lat} lng={selected.lng} />
            <LastMilePanel lat={selected.lat} lng={selected.lng} />
          </>
        )}
      </main>
      <aside className="border-l p-4">
        {selected && <AgentFeed lat={selected.lat} lng={selected.lng} />}
      </aside>
    </div>
  );
}
