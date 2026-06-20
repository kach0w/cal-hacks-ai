import type { FindingStatus } from "../types";

const STYLES: Record<FindingStatus, string> = {
  CONFIRMED: "bg-green-100 text-green-800",
  CANDIDATE: "bg-amber-100 text-amber-800",
  REPORTED: "bg-slate-100 text-slate-700",
};

/** CONFIRMED = seen AND independently corroborated. The tool never launders a guess. */
export default function ConfidenceBadge({ status }: { status: FindingStatus }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {status}
    </span>
  );
}
