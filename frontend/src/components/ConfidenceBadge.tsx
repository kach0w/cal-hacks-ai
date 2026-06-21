import type { FindingStatus } from "../types";
import { Check, Eye, FileWarning } from "./icons";

const META: Record<
  FindingStatus,
  { ring: string; text: string; dot: string; Icon: typeof Check; label: string }
> = {
  CONFIRMED: {
    ring: "border-confirmed/30 bg-confirmed/10",
    text: "text-confirmed",
    dot: "bg-confirmed",
    Icon: Check,
    label: "Corroborated",
  },
  CANDIDATE: {
    ring: "border-candidate/30 bg-candidate/10",
    text: "text-candidate",
    dot: "bg-candidate",
    Icon: Eye,
    label: "Not corroborated",
  },
  REPORTED: {
    ring: "border-candidate/30 bg-candidate/10",
    text: "text-candidate",
    dot: "bg-candidate",
    Icon: Eye,
    label: "Not corroborated",
  },
};

/** CONFIRMED = seen AND independently corroborated. The tool never launders a guess. */
export default function ConfidenceBadge({
  status,
  size = "md",
}: {
  status: FindingStatus;
  size?: "sm" | "md";
}) {
  const m = META[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-semibold tracking-wide ${m.ring} ${m.text} ${
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-[11px]"
      }`}
    >
      <m.Icon className="h-3 w-3" />
      {m.label}
    </span>
  );
}

export { META as STATUS_META };
