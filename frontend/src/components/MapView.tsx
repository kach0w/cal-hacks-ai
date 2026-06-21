import { useState } from "react";
import MapboxMap from "./MapboxMap";
import { forwardGeocode, reverseGeocode, MAPBOX_ENABLED, type GeoPlace } from "../lib/mapbox";
import { ShieldPin, Search, Eye, Link, Megaphone, ArrowRight, MapPin } from "./icons";

/**
 * Entry point — the selector, NOT the deliverable. A live 3D Mapbox map is the
 * centerpiece: click an intersection (reverse-geocoded) or search an address
 * (forward-geocoded), then send it into the analysis pipeline.
 */

const DEMO: GeoPlace = {
  lat: 37.7706,
  lng: -122.2215,
  label: "International Blvd & 35th Ave, Oakland, CA",
};

const SIGNALS = [
  {
    Icon: Eye,
    title: "Grounded, not generated",
    body: "Every marker sits on the real satellite & Street View — traceable to a visual observation and an independent record.",
  },
  {
    Icon: Search,
    title: "Honest by design",
    body: "Vision runs blind to the complaints first, then corroboration is matched separately. Two genuinely independent signals.",
  },
  {
    Icon: Link,
    title: "It closes the loop",
    body: "Diagnosis wires straight into the ask, the grant, the official to email, and proof the city already knew.",
  },
];

export default function MapView({
  onSelect,
}: {
  onSelect: (p: { lat: number; lng: number }) => void;
}) {
  const [coords, setCoords] = useState("");
  const [picked, setPicked] = useState<GeoPlace | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const parts = coords.split(",").map((s) => parseFloat(s.trim()));
    if (parts.length !== 2 || parts.some(isNaN)) {
      setError("Paste as: lat, lng — e.g. 37.86870, -122.25917");
      return;
    }
    setError(null);
    onSelect({ lat: parts[0], lng: parts[1] });
  }

  // Map click: drop the pin immediately, then fill in the address label.
  async function handlePick(lng: number, lat: number) {
    setError(null);
    setPicked({ lng, lat, label: "Locating address…" });
    const label = await reverseGeocode(lng, lat).catch(() => null);
    setPicked({ lng, lat, label: label ?? `${lat.toFixed(5)}, ${lng.toFixed(5)}` });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto flex max-w-6xl flex-col px-6 pb-24 pt-8">
        {/* Top bar */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand/15 text-brand ring-1 ring-brand/30">
              <ShieldPin className="h-5 w-5" />
            </span>
            <span className="text-[15px] font-semibold tracking-tight text-gray-900">
              Safe<span className="text-brand">Streets</span>
            </span>
          </div>
          <span className="hidden items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-500 sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-confirmed animate-blink" />
            Multi-agent street analysis · live
          </span>
        </header>

        {/* Hero */}
        <section className="mx-auto mt-16 max-w-3xl text-center">
          <span className="eyebrow inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5">
            <Megaphone className="h-3.5 w-3.5 text-brand" />
            Advocacy infrastructure for safer streets
          </span>
          <h1 className="mt-6 text-balance text-4xl font-bold leading-[1.05] tracking-tight text-gray-900 sm:text-6xl">
            See the street.
            <br />
            Name the fix. <span className="text-amber-500">Move the city.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-pretty text-base leading-relaxed text-gray-500 sm:text-lg">
            Pick an intersection. SafeStreets reads the actual street, tells you exactly what's
            physically wrong, and hands you the ask, the grant, the official — and the record the
            city can't quietly bury.
          </p>

          {/* Search */}
          <form
            className="mx-auto mt-9 flex max-w-xl flex-col items-stretch gap-2.5 sm:flex-row"
            onSubmit={handleSearch}
          >
            <input
              value={coords}
              onChange={(e) => setCoords(e.target.value)}
              placeholder="lat, lng — e.g. 37.86870, -122.25917"
              className="flex-1 rounded-xl border border-gray-200 bg-white py-3.5 px-4 text-[15px] text-gray-900 placeholder:text-gray-500 backdrop-blur-xl transition-colors focus:border-brand/50"
            />
            <button type="submit" className="btn-primary py-3.5">
              Analyze <ArrowRight className="h-4 w-4" />
            </button>
          </form>
          {error && <p className="mt-3 text-sm text-signal">{error}</p>}
        </section>

        {/* Live 3D map */}
        <section className="mt-10">
          <div className="panel relative overflow-hidden">
            {MAPBOX_ENABLED ? (
              <>
                <MapboxMap
                  center={[DEMO.lng, DEMO.lat]}
                  picked={picked}
                  onPick={handlePick}
                  className="h-[460px] w-full sm:h-[520px]"
                />
                {/* Hint */}
                <div className="pointer-events-none absolute left-4 top-4 inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-500 backdrop-blur">
                  <MapPin className="h-3.5 w-3.5 text-brand" />
                  Click any intersection to select it
                </div>

                {/* Picked action card */}
                {picked && (
                  <div className="absolute inset-x-4 bottom-4 mx-auto max-w-lg animate-fade-up rounded-xl border border-gray-200 bg-white p-4 backdrop-blur-xl">
                    <div className="flex items-center gap-3">
                      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-brand/15 text-brand ring-1 ring-brand/30">
                        <MapPin className="h-5 w-5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-gray-900">{picked.label}</p>
                        <p className="font-mono text-[11px] text-gray-500">
                          {picked.lat.toFixed(5)}, {picked.lng.toFixed(5)}
                        </p>
                      </div>
                      <button
                        className="btn-primary shrink-0"
                        onClick={() => onSelect({ lat: picked.lat, lng: picked.lng })}
                      >
                        Analyze
                        <ArrowRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              // Graceful fallback when no token is configured.
              <div className="flex h-[420px] flex-col items-center justify-center gap-4 bg-dots p-6 text-center">
                <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand/10 text-brand ring-1 ring-brand/20">
                  <MapPin className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-gray-900">Map needs a Mapbox token</p>
                  <p className="mt-1 text-sm text-gray-500">
                    Add <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs">VITE_MAPBOX_TOKEN</code>{" "}
                    to <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs">frontend/.env</code> to
                    enable the live 3D map.
                  </p>
                </div>
                <button className="btn-ghost" onClick={() => onSelect({ lat: DEMO.lat, lng: DEMO.lng })}>
                  <MapPin className="h-4 w-4" />
                  Continue with the demo intersection
                </button>
              </div>
            )}
          </div>

          {MAPBOX_ENABLED && (
            <button
              onClick={() => setPicked(DEMO)}
              className="group mx-auto mt-4 flex items-center gap-2 text-sm text-gray-500 transition-colors hover:text-brand cursor-pointer"
            >
              <MapPin className="h-4 w-4" />
              Or jump to the demo intersection
              <span className="text-gray-500 transition-transform group-hover:translate-x-0.5">↗</span>
            </button>
          )}
        </section>

        {/* Trust signals */}
        <section className="mt-20 grid gap-4 sm:grid-cols-3">
          {SIGNALS.map((s, i) => (
            <article
              key={s.title}
              className="panel group p-5 transition-colors hover:border-gray-300 animate-fade-up"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand/10 text-brand ring-1 ring-brand/20 transition-colors group-hover:bg-brand/15">
                <s.Icon className="h-5 w-5" />
              </span>
              <h3 className="mt-4 text-sm font-semibold text-gray-900">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-gray-500">{s.body}</p>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}
