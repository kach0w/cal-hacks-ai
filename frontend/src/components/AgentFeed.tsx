import { useAnalysis } from "../hooks/useAnalysis";

/**
 * The 'wow moment': a live log that reads like investigative reporting, including the
 * Stage 1 (blind) -> Stage 2 (corroboration) -> accountability beats.
 */
export default function AgentFeed({ lat, lng }: { lat: number; lng: number }) {
  const { events, done } = useAnalysis(lat, lng);
  return (
    <div className="font-mono text-xs space-y-1">
      <div className="mb-2 font-sans font-semibold">Live analysis</div>
      {events.map((e, i) => (
        <div key={i} className="text-slate-700">
          <span className="text-slate-400">[{String(e.agent)}]</span> {String(e.msg)}
        </div>
      ))}
      {done && <div className="pt-2 font-sans text-green-700">Analysis complete.</div>}
    </div>
  );
}
