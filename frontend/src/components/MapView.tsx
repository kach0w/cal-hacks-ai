/**
 * Mapbox GL selector — the entry point, NOT the deliverable.
 * TODO: render mapbox-gl, let the user click an intersection or type an address,
 * show previously analyzed intersections colored by severity, cluster corridors.
 */
export default function MapView({ onSelect }: { onSelect: (p: { lat: number; lng: number }) => void }) {
  return (
    <div className="rounded border p-6">
      <p className="text-sm text-slate-600">Map selector goes here (mapbox-gl).</p>
      {/* TODO: replace with a real map + click handler */}
      <button
        className="mt-3 rounded bg-slate-900 px-3 py-1.5 text-sm text-white"
        onClick={() => onSelect({ lat: 37.7706, lng: -122.2215 })}
      >
        Use demo intersection (Oakland International &amp; 35th)
      </button>
    </div>
  );
}
