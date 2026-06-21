import { useState } from "react";
import MapboxMap from "./MapboxMap";
import { reverseGeocode, MAPBOX_ENABLED, type GeoPlace } from "../lib/mapbox";
import { ShieldPin, ArrowRight, MapPin } from "./icons";

const DEMO: GeoPlace = {
  lat: 37.7706,
  lng: -122.2215,
  label: "International Blvd & 35th Ave, Oakland, CA",
};

export default function MapView({
  onSelect,
}: {
  onSelect: (p: { lat: number; lng: number }) => void;
}) {
  const DEMO_COORDS = "37.86870873221915, -122.25917423795075";
  const [coords, setCoords] = useState(DEMO_COORDS);
  const [picked, setPicked] = useState<GeoPlace | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const parts = coords.split(",").map((s) => parseFloat(s.trim()));
    if (parts.length !== 2 || parts.some(isNaN)) {
      setError("Enter as: lat, lng");
      return;
    }
    setError(null);
    onSelect({ lat: parts[0], lng: parts[1] });
  }

  async function handlePick(lng: number, lat: number) {
    setError(null);
    setPicked({ lng, lat, label: "Locating…" });
    const label = await reverseGeocode(lng, lat).catch(() => null);
    setPicked({ lng, lat, label: label ?? `${lat.toFixed(5)}, ${lng.toFixed(5)}` });
  }

  return (
    <div className="min-h-screen bg-dots" style={{ background: "#1a1f3d" }}>
      <div className="mx-auto flex max-w-5xl flex-col px-6 pb-24 pt-8">

        {/* Top bar */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center" style={{ background: "#e8c000", border: "3px solid #b89000" }}>
              <ShieldPin className="h-5 w-5" style={{ color: "#1a1f3d" }} />
            </span>
            <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#f0ece0" }}>
              SAFE<span style={{ color: "#e8c000" }}>STREETS</span>
            </span>
          </div>
          <span className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5" style={{ border: "2px solid #2c3060", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0" }}>
            <span className="h-1.5 w-1.5 animate-blink" style={{ background: "#38a832", display: "inline-block" }} />
            LIVE · MULTI-AGENT
          </span>
        </header>

        {/* Hero */}
        <section className="mx-auto mt-14 max-w-3xl text-center">
          {/* Pokemon-style dialogue box title */}
          <div className="mx-auto mb-8 max-w-2xl p-6 text-left" style={{ background: "#f0ece0", border: "4px solid #2c3060", boxShadow: "6px 6px 0 #0f1428", color: "#1a1f3d" }}>
            <p style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#6070a0", marginBottom: 12 }}>
              ▶ SAFESTREETS used ANALYZE!
            </p>
            <h1 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 14, lineHeight: 1.8, color: "#1a1f3d" }}>
              SEE THE STREET.<br />
              NAME THE FIX.<br />
              <span style={{ color: "#e8c000" }}>MOVE THE CITY.</span>
            </h1>
            <p style={{ fontFamily: '"VT323", monospace', fontSize: 20, marginTop: 14, color: "#3a3f60", lineHeight: 1.5 }}>
              Pick an intersection. SafeStreets reads the real street, names what's wrong,
              and generates the ask, the grant, and the record the city can't quietly bury.
            </p>
          </div>

          {/* Search */}
          <form
            className="mx-auto mt-6 flex max-w-xl items-stretch gap-2"
            onSubmit={handleSearch}
          >
            <input
              value={coords}
              onChange={(e) => setCoords(e.target.value)}
              placeholder={DEMO_COORDS}
              style={{
                flex: 1,
                background: "#f0ece0",
                border: "3px solid #2c3060",
                color: "#1a1f3d",
                fontFamily: '"Press Start 2P", monospace',
                fontSize: 8,
                padding: "14px 12px",
                outline: "none",
              }}
            />
            <button
              type="submit"
              className="btn-primary"
              style={{ padding: "0", width: 42, height: 42, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, alignSelf: "center" }}
            >
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </form>
          {error && (
            <p style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#e84040", marginTop: 10 }}>
              ✗ {error}
            </p>
          )}
        </section>

        {/* Map */}
        <section className="mt-8">
          <div style={{ border: "4px solid #2c3060", boxShadow: "6px 6px 0 #0f1428", position: "relative", overflow: "hidden" }}>
            {MAPBOX_ENABLED ? (
              <>
                <MapboxMap
                  center={[DEMO.lng, DEMO.lat]}
                  picked={picked}
                  onPick={handlePick}
                  className="h-[460px] w-full sm:h-[520px]"
                />
                <div
                  className="pointer-events-none absolute left-3 top-3 inline-flex items-center gap-2 px-3 py-1.5"
                  style={{ background: "#f0ece0", border: "2px solid #2c3060", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#3a3f60" }}
                >
                  <MapPin className="h-3 w-3" style={{ color: "#e8c000" }} />
                  CLICK INTERSECTION
                </div>

                {picked && (
                  <div className="absolute inset-x-3 bottom-3 mx-auto max-w-lg animate-fade-up p-4" style={{ background: "#f0ece0", border: "3px solid #2c3060", boxShadow: "4px 4px 0 #0f1428" }}>
                    <div className="flex items-center gap-3">
                      <span className="grid h-10 w-10 shrink-0 place-items-center" style={{ background: "#e8c000", border: "2px solid #b89000" }}>
                        <MapPin className="h-5 w-5" style={{ color: "#1a1f3d" }} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>{picked.label}</p>
                        <p style={{ fontFamily: '"VT323", monospace', fontSize: 16, color: "#6070a0", marginTop: 2 }}>
                          {picked.lat.toFixed(5)}, {picked.lng.toFixed(5)}
                        </p>
                      </div>
                      <button
                        className="btn-primary shrink-0"
                        style={{ padding: "14px 24px", fontSize: 10, letterSpacing: 2 }}
                        onClick={() => onSelect({ lat: picked.lat, lng: picked.lng })}
                      >
                        SCAN &nbsp;<ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex h-[420px] flex-col items-center justify-center gap-5 p-6 text-center bg-dots">
                <span className="grid h-14 w-14 place-items-center" style={{ background: "#e8c000", border: "3px solid #b89000" }}>
                  <MapPin className="h-7 w-7" style={{ color: "#1a1f3d" }} />
                </span>
                <div>
                  <p style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 9, color: "#f0ece0" }}>MAP TOKEN NEEDED</p>
                  <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#6070a0", marginTop: 8 }}>
                    Add VITE_MAPBOX_TOKEN to frontend/.env
                  </p>
                </div>
                <button className="btn-ghost" onClick={() => onSelect({ lat: DEMO.lat, lng: DEMO.lng })}>
                  <MapPin className="h-4 w-4" />
                  USE DEMO INTERSECTION
                </button>
              </div>
            )}
          </div>

          {MAPBOX_ENABLED && (
            <button
              onClick={() => setPicked(DEMO)}
              className="mx-auto mt-4 flex items-center gap-2 cursor-pointer"
              style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", background: "none", border: "none" }}
            >
              <MapPin className="h-3 w-3" />
              or jump to demo intersection ↗
            </button>
          )}
        </section>

        {/* Feature pills */}
        <section className="mt-12 grid gap-4 sm:grid-cols-3">
          {[
            { icon: "👁", title: "GROUNDED", body: "Every marker sits on real satellite + Street View imagery" },
            { icon: "🔗", title: "HONEST", body: "Vision runs blind first, then corroboration matched separately" },
            { icon: "📋", title: "ACTIONABLE", body: "Diagnosis wires straight into the ask, grant, and official to email" },
          ].map((s, i) => (
            <div
              key={s.title}
              className="p-5 animate-fade-up"
              style={{ background: "#f0ece0", border: "3px solid #2c3060", boxShadow: "4px 4px 0 #0f1428", color: "#1a1f3d", animationDelay: `${i * 80}ms` }}
            >
              <div style={{ fontSize: 28 }}>{s.icon}</div>
              <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, marginTop: 12, marginBottom: 8 }}>{s.title}</h3>
              <p style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#3a3f60", lineHeight: 1.4 }}>{s.body}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
