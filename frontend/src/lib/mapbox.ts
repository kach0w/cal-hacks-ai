/**
 * Mapbox API helpers — access token + Geocoding API (v6) calls.
 * The token is read from import.meta.env.VITE_MAPBOX_TOKEN at build time by Vite.
 */

export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN ?? "";
export const MAPBOX_ENABLED = MAPBOX_TOKEN.length > 0;

/** The default Mapbox 3D template (buildings, terrain, lighting out of the box). */
export const MAPBOX_STYLE = "mapbox://styles/mapbox/standard";

export interface GeoPlace {
  lng: number;
  lat: number;
  label: string;
}

/** Address / intersection text -> coordinates. */
export async function forwardGeocode(query: string): Promise<GeoPlace | null> {
  if (!query.trim() || !MAPBOX_ENABLED) return null;
  const url =
    `https://api.mapbox.com/search/geocode/v6/forward` +
    `?q=${encodeURIComponent(query)}&limit=1&types=address,street,poi&access_token=${MAPBOX_TOKEN}`;
  const res = await fetch(url);
  if (!res.ok) return null;
  const data = await res.json();
  const f = data.features?.[0];
  if (!f) return null;
  const [lng, lat] = f.geometry.coordinates as [number, number];
  return { lng, lat, label: f.properties?.full_address ?? f.properties?.name ?? query };
}

/** Coordinates -> a human-readable address label. */
export async function reverseGeocode(lng: number, lat: number): Promise<string | null> {
  if (!MAPBOX_ENABLED) return null;
  const url =
    `https://api.mapbox.com/search/geocode/v6/reverse` +
    `?longitude=${lng}&latitude=${lat}&limit=1&access_token=${MAPBOX_TOKEN}`;
  const res = await fetch(url);
  if (!res.ok) return null;
  const data = await res.json();
  return data.features?.[0]?.properties?.full_address ?? data.features?.[0]?.properties?.name ?? null;
}
