import type { NamedZone } from "../types";

// Must match backend vision/geometry.py. North-up top-down image.
const ZONE_FRACTIONS: Record<NamedZone, [number, number]> = {
  NW: [0.3, 0.3], NE: [0.7, 0.3], SW: [0.3, 0.7], SE: [0.7, 0.7],
  N_LEG: [0.5, 0.15], S_LEG: [0.5, 0.85], E_LEG: [0.85, 0.5], W_LEG: [0.15, 0.5],
  CENTER: [0.5, 0.5],
};

export function zoneToPercent(zone: NamedZone): { left: string; top: string } {
  const [fx, fy] = ZONE_FRACTIONS[zone] ?? ZONE_FRACTIONS["CENTER"];
  return { left: `${fx * 100}%`, top: `${fy * 100}%` };
}
