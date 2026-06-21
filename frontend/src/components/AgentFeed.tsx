import { useEffect, useRef } from "react";
import { useAnalysis } from "../hooks/useAnalysis";
import type { ProgressEvent } from "../types";
import { Eye, Search, FileWarning, Check } from "./icons";

/**
 * The 'wow moment': a live, terminal-style log that reads like investigative
 * reporting and makes the blind → corroborate → accountability beats explicit.
 * The user watches the system commit to what it saw before it knew what residents reported.
 */

type Stage = "dispatch" | "vision" | "corroborate" | "accountability";

function stageOf(e: ProgressEvent): Stage {
  const a = `${e.agent ?? ""}`.toLowerCase();
  const s = `${(e as Record<string, unknown>).stage ?? ""}`.toLowerCase();
  const hay = `${a} ${s}`;
  if (hay.includes("stage 1") || hay.includes("vision")) return "vision";
  if (hay.includes("stage 2") || hay.includes("corrobor")) return "corroborate";
  if (hay.includes("account")) return "accountability";
  return "dispatch";
}

const STAGE_META: Record<Stage, { label: string; accent: string; Icon: typeof Eye }> = {
  dispatch: { label: "Dispatch", accent: "text-slate-400", Icon: Search },
  vision: { label: "Stage 1 · blind vision", accent: "text-brand", Icon: Eye },
  corroborate: { label: "Stage 2 · corroboration", accent: "text-confirmed", Icon: Check },
  accountability: { label: "Accountability", accent: "text-reported", Icon: FileWarning },
};

/** Highlight the verdict tokens so the eye lands on CONFIRMED / REPORTED / HIGH. */
function decorate(msg: string) {
  const parts = msg.split(/(CONFIRMED|REPORTED|CANDIDATE|HIGH|MEDIUM|LOW)/g);
  return parts.map((p, i) => {
    const cls =
      p === "CONFIRMED"
        ? "text-confirmed font-semibold"
        : p === "REPORTED"
          ? "text-reported font-semibold"
          : p === "CANDIDATE"
            ? "text-candidate font-semibold"
            : p === "HIGH"
              ? "text-confirmed"
              : p === "MEDIUM"
                ? "text-candidate"
                : p === "LOW"
                  ? "text-slate-500"
                  : "";
    return cls ? (
      <span key={i} className={cls}>
        {p}
      </span>
    ) : (
      <span key={i}>{p}</span>
    );
  });
}

export default function AgentFeed({ lat, lng }: { lat: number; lng: number }) {
  const { events, done } = useAnalysis(lat, lng);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length, done]);

  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      {/* Terminal chrome */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-signal/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-candidate/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-confirmed/70" />
          </span>
          <span className="ml-1 font-mono text-xs text-slate-400">live agent feed</span>
        </div>
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-slate-500">
          <span
            className={`h-1.5 w-1.5 rounded-full ${done ? "bg-confirmed" : "bg-brand animate-blink"}`}
          />
          {done ? "complete" : "running"}
        </span>
      </div>

      {/* Log */}
      <div
        ref={scrollRef}
        className="relative flex-1 space-y-0.5 overflow-y-auto px-4 py-3 font-mono text-[12.5px] leading-relaxed"
        aria-live="polite"
      >
        {events.length === 0 && (
          <div className="space-y-2 pt-2">
            {[90, 70, 80, 60].map((w, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-white/10" />
                <div
                  className="h-3 rounded bg-white/[0.06]"
                  style={{ width: `${w}%`, animation: "blink 1.4s infinite", animationDelay: `${i * 120}ms` }}
                />
              </div>
            ))}
            <p className="pt-3 text-slate-500">Connecting to orchestrator…</p>
          </div>
        )}

        {events.map((e, i) => {
          const stage = stageOf(e);
          const m = STAGE_META[stage];
          const prevStage = i > 0 ? stageOf(events[i - 1]) : null;
          const isNewStage = stage !== prevStage;
          return (
            <div key={i} className="animate-fade-up">
              {isNewStage && (
                <div className={`mt-3 flex items-center gap-2 first:mt-0 ${m.accent}`}>
                  <m.Icon className="h-3.5 w-3.5" />
                  <span className="text-[11px] font-semibold uppercase tracking-[0.14em]">
                    {m.label}
                  </span>
                  <span className="h-px flex-1 bg-white/10" />
                </div>
              )}
              <div className="flex gap-2 pl-0.5 text-slate-300">
                <span className={`select-none ${m.accent}`}>›</span>
                <span>
                  <span className="text-slate-500">{String(e.agent)}: </span>
                  {decorate(String(e.msg))}
                </span>
              </div>
            </div>
          );
        })}

        {events.length > 0 && !done && (
          <div className="flex items-center gap-2 pl-3 pt-1 text-brand">
            <span className="inline-block h-3.5 w-2 animate-blink bg-brand" />
          </div>
        )}

        {done && (
          <div className="mt-4 flex items-center gap-2 rounded-lg border border-confirmed/25 bg-confirmed/10 px-3 py-2 font-sans text-xs text-confirmed">
            <Check className="h-4 w-4" />
            Case assembled — every CONFIRMED finding is two independent signals.
          </div>
        )}
      </div>
    </div>
  );
}
