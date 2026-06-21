import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import { MAPBOX_TOKEN, MAPBOX_STYLE } from "../lib/mapbox";

interface Props {
  center?: [number, number];
  zoom?: number;
  picked: { lng: number; lat: number } | null;
  onPick: (lng: number, lat: number) => void;
  className?: string;
}

const ALAMEDA_CENTER: [number, number] = [-122.05, 37.65];

export default function MapboxMap({ picked, onPick, className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapboxgl.accessToken = MAPBOX_TOKEN;

    // Start centered on county; fly to geolocation once we have it
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: MAPBOX_STYLE,
      center: ALAMEDA_CENTER,
      zoom: 10,
      pitch: 45,
      bearing: -17,
      antialias: true,
      attributionControl: false,
    });

    map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "top-right");
    map.addControl(new mapboxgl.AttributionControl({ compact: true }), "bottom-right");

    map.on("click", (e) => {
      const features = map.queryRenderedFeatures(e.point, { layers: ["alameda-intersections"] });
      if (features.length) {
        const f = features[0];
        const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
        onPickRef.current(coords[0], coords[1]);
      } else {
        onPickRef.current(e.lngLat.lng, e.lngLat.lat);
      }
    });

    map.on("mouseenter", "alameda-intersections", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "alameda-intersections", () => {
      map.getCanvas().style.cursor = "";
    });

    map.on("style.load", () => {
      try {
        (map as unknown as {
          setConfigProperty: (s: string, k: string, v: string) => void;
        }).setConfigProperty("basemap", "lightPreset", "dusk");
      } catch { /* older style versions */ }

      // Load Alameda County dangerous intersections
      fetch("/alameda_intersections.geojson")
        .then((r) => r.json())
        .then((geojson) => {
          if (map.getSource("alameda-intersections")) return;

          map.addSource("alameda-intersections", {
            type: "geojson",
            data: geojson,
            cluster: true,
            clusterMaxZoom: 13,
            clusterRadius: 30,
          });

          // Clustered circles
          map.addLayer({
            id: "alameda-clusters",
            type: "circle",
            source: "alameda-intersections",
            filter: ["has", "point_count"],
            paint: {
              "circle-color": [
                "step", ["get", "point_count"],
                "#e84040", 10,
                "#e8a000", 50,
                "#e84040"
              ],
              "circle-radius": ["step", ["get", "point_count"], 14, 10, 20, 50, 26],
              "circle-opacity": 0.85,
              "circle-stroke-width": 2,
              "circle-stroke-color": "#f0ece0",
            },
          });

          // Cluster count labels
          map.addLayer({
            id: "alameda-cluster-count",
            type: "symbol",
            source: "alameda-intersections",
            filter: ["has", "point_count"],
            layout: {
              "text-field": "{point_count_abbreviated}",
              "text-size": 11,
              "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
            },
            paint: { "text-color": "#f0ece0" },
          });

          // Individual intersection dots
          map.addLayer({
            id: "alameda-intersections",
            type: "circle",
            source: "alameda-intersections",
            filter: ["!", ["has", "point_count"]],
            paint: {
              "circle-radius": [
                "interpolate", ["linear"], ["get", "danger_score"],
                0, 4,
                25, 9,
              ],
              "circle-color": [
                "interpolate", ["linear"], ["get", "danger_score"],
                0, "#e8c000",
                15, "#e84040",
              ],
              "circle-opacity": 0.8,
              "circle-stroke-width": 1.5,
              "circle-stroke-color": "#1a1f3d",
            },
          });

          // Expand cluster on click
          map.on("click", "alameda-clusters", (e) => {
            const features = map.queryRenderedFeatures(e.point, { layers: ["alameda-clusters"] });
            if (!features.length) return;
            const clusterId = features[0].properties!.cluster_id;
            (map.getSource("alameda-intersections") as mapboxgl.GeoJSONSource)
              .getClusterExpansionZoom(clusterId, (err, z) => {
                if (err || z == null) return;
                map.easeTo({
                  center: (features[0].geometry as GeoJSON.Point).coordinates as [number, number],
                  zoom: z,
                });
              });
          });
        })
        .catch((e) => console.warn("Could not load alameda intersections:", e));
    });

    // Fly to current location
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          // Only fly if within Alameda County bounding box
          if (latitude > 37.45 && latitude < 37.92 && longitude > -122.38 && longitude < -121.47) {
            map.flyTo({ center: [longitude, latitude], zoom: 12, duration: 1800, essential: true });
          }
        },
        () => { /* denied — stay on county center */ },
        { timeout: 5000 }
      );
    }

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fly to and mark picked location
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
