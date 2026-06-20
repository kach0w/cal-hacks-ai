import { useState } from "react";
import { submitReport } from "../api/client";

/** Resident submission: a current photo + description that fills data deserts, supersedes
 *  stale Street View, and counts toward the corridor coalition. */
export default function ResidentSubmit({ lat, lng }: { lat: number; lng: number }) {
  const [desc, setDesc] = useState("");
  const [count, setCount] = useState<number | null>(null);

  async function send() {
    const r = await submitReport({ lat, lng, description: desc });
    setCount(r.coalition_count);
  }

  return (
    <div className="rounded border p-4 text-sm space-y-2">
      <textarea className="w-full rounded border p-2" placeholder="What's wrong here?"
        value={desc} onChange={(e) => setDesc(e.target.value)} />
      {/* TODO: photo upload -> photo_url */}
      <button className="rounded bg-slate-900 px-3 py-1.5 text-white" onClick={send}>Submit</button>
      {count !== null && <p className="text-green-700">{count} residents have flagged this corridor.</p>}
    </div>
  );
}
