import { useEffect, useRef, useState } from "react";
import { analyzeIntersection } from "../api/client";
import type { AnalysisResult } from "../types";

export function useIntersection(lat: number, lng: number) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let alive = true;

    function stopPolling() {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    }

    analyzeIntersection(lat, lng).then((r) => {
      if (!alive) return;
      setResult(r);
      setLoading(false);

      // Poll every 5s until renders arrive (they're generated in background)
      if (!r?.renders?.length) {
        pollRef.current = setInterval(async () => {
          if (!alive) { stopPolling(); return; }
          try {
            const updated = await analyzeIntersection(lat, lng);
            if (!alive) return;
            if (updated) setResult(updated);
            if (updated?.renders?.length) stopPolling();
          } catch { /* ignore poll errors */ }
        }, 5000);
      }
    });

    return () => {
      alive = false;
      stopPolling();
    };
  }, [lat, lng]);

  return { result, loading };
}
