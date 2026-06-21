import type { AnalysisResult, ProgressEvent } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getIntersection(lat: number, lng: number): Promise<AnalysisResult | null> {
  const res = await fetch(`${BASE}/intersection?lat=${lat}&lng=${lng}`);
  if (!res.ok) return null;
  return res.json();
}

export async function analyzeIntersection(lat: number, lng: number): Promise<AnalysisResult | null> {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function submitReport(body: {
  lat: number; lng: number; description: string; zone_hint?: string; photo_url?: string;
}): Promise<{ coalition_count: number }> {
  const res = await fetch(`${BASE}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

/** Subscribe to the SSE live agent feed. Returns an unsubscribe fn. */
export function streamAnalysis(
  lat: number,
  lng: number,
  onEvent: (e: ProgressEvent) => void,
  onDone: () => void
): () => void {
  const es = new EventSource(`${BASE}/analyze/stream?lat=${lat}&lng=${lng}`);
  es.addEventListener("progress", (ev) => onEvent(JSON.parse((ev as MessageEvent).data)));
  es.addEventListener("done", () => { onDone(); es.close(); });
  es.onerror = () => es.close();
  return () => es.close();
}
