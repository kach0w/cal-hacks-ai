import { useEffect, useRef, useState } from "react";
import { streamAnalysis } from "../api/client";
import type { ProgressEvent } from "../types";

/** Subscribes to the SSE agent feed and accumulates progress events. */
export function useAnalysis(lat: number, lng: number) {
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [done, setDone] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const stop = streamAnalysis(
      lat, lng,
      (e) => setEvents((prev) => [...prev, e]),
      () => setDone(true)
    );
    return stop;
  }, [lat, lng]);

  return { events, done };
}
