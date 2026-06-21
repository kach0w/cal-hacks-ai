import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import { MAPBOX_TOKEN, MAPBOX_STYLE } from "../lib/mapbox";

/**
 * Interactive Mapbox GL map using the default 3D "Standard" template (3D buildings,
 * terrain, lighting). Single source of truth is `picked`: the map flies to it and drops
 * a marker; clicking the map emits coordinates back up via `onPick`.
 */
interface Props {
  center: [number, number];
  zoom?: number;
  picked: { lng: number; lat: number } | null;
  onPick: (lng: number, lat: number) => void;
  className?: string;
}

export default function MapboxMap({ center, zoom = 11, picked, onPick, className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;

  // Initialize the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: MAPBOX_STYLE,
      center,
      zoom,
      pitch: 55, // tilt for the 3D view
      bearing: -17,
      antialias: true,
      attributionControl: false,
    });

    map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "top-right");
    map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-right");
    map.on("click", (e) => onPickRef.current(e.lngLat.lng, e.lngLat.lat));

    // Standard style is 3D already; nudge the light preset to match the dark UI.
    map.on("style.load", () => {
      try {
        (map as unknown as {
          setConfigProperty: (s: string, k: string, v: string) => void;
        }).setConfigProperty("basemap", "lightPreset", "dusk");
      } catch {
        /* older style versions ignore this */
      }
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // center/zoom are initial-only by design
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fly to and mark the picked location whenever it changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !picked) return;

    map.flyTo({
      center: [picked.lng, picked.lat],
      zoom: 16,
      pitch: 55,
      duration: 1500,
      essential: true,
    });

    if (!markerRef.current) {
      markerRef.current = new mapboxgl.Marker({ color: "#F59E0B" });
    }
    markerRef.current.setLngLat([picked.lng, picked.lat]).addTo(map);
  }, [picked?.lng, picked?.lat]);

  return <div ref={containerRef} className={className} aria-label="Interactive map" />;
}
