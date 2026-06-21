import { useEffect, useState } from "react";
import { analyzeIntersection } from "../api/client";
import type { AnalysisResult } from "../types";

export function useIntersection(lat: number, lng: number) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    analyzeIntersection(lat, lng).then((r) => {
      if (alive) { setResult(r); setLoading(false); }
    });
    return () => { alive = false; };
  }, [lat, lng]);

  return { result, loading };
}
