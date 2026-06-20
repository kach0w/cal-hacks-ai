/**
 * The half that changes outcomes: The Ask, The Money (matching grant program), The
 * Messenger (who decides + next meeting + draft message), coalition count, and the
 * accountability record. TODO: fetch the assembled packet from the backend.
 */
export default function LastMilePanel({ lat, lng }: { lat: number; lng: number }) {
  return (
    <div className="rounded border p-4 text-sm space-y-3">
      <h3 className="font-semibold">From finding to funded</h3>
      <p className="text-slate-500">The Ask, the matching grant (SS4A / HSIP), who decides,
        and the accountability record render here.</p>
      <p className="text-xs text-slate-400">({lat.toFixed(4)}, {lng.toFixed(4)}) — TODO: wire packet endpoint</p>
    </div>
  );
}
