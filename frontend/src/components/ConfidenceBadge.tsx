import type { FindingStatus } from "../types";
import { Check, Eye } from "./icons";

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
  const isConfirmed = status === "CONFIRMED";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        border: `2px solid ${isConfirmed ? "#38a832" : "#e84040"}`,
        background: isConfirmed ? "rgba(56,168,50,0.12)" : "rgba(232,64,64,0.12)",
        color: isConfirmed ? "#38a832" : "#e84040",
        fontFamily: '"Press Start 2P", monospace',
        fontSize: size === "sm" ? 6 : 7,
        padding: "3px 8px",
      }}
    >
      <m.Icon className="h-3 w-3" />
      {m.label}
    </span>
  );
}

export { META as STATUS_META };
