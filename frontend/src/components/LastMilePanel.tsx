import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import OnePagerExport from "./OnePagerExport";
import type { AccountabilityEvent } from "../types";
import { Scale, Banknote, Megaphone, Users, FileWarning, Calendar, Building, ArrowRight } from "./icons";

/**
 * The half that changes outcomes: The Ask, The Money (matching grant), The Messenger
 * (who decides + next meeting), the coalition count, and the accountability record.
 * Assembled from the analysis result; cards degrade gracefully when a field is absent.
 */

const ACTION_META: Record<AccountabilityEvent["action_status"], { label: string; cls: string }> = {
  no_action_recorded: { label: "No action recorded", cls: "text-red-600 border-red-200 bg-red-50" },
  action_recorded: { label: "Action taken", cls: "text-green-700 border-confirmed/30 bg-green-50" },
  unknown: { label: "Unknown", cls: "text-gray-400 border-white/15 bg-gray-100" },
};

function fmtCost(low: number | null, high: number | null, unit: string) {
  if (low == null && high == null) return "";
  const f = (n: number) => (n >= 1000 ? `$${(n / 1000).toFixed(n % 1000 ? 1 : 0)}k` : `$${n}`);
  const r = low === high || high == null ? f(low!) : `${f(low!)}–${f(high!)}`;
  return ` — est. ${r}/${unit}`;
}

export default function LastMilePanel({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);

  if (loading || !result) {
    return (
      <section className="panel p-5">
        <Header />
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      </section>
    );
  }

  // The Ask: prefer a CONFIRMED finding that carries an intervention.
  const ranked = [...result.findings].sort((a, b) =>
    a.status === "CONFIRMED" && b.status !== "CONFIRMED" ? -1 : 1,
  );
  const top = ranked.find((f) => f.intervention) ?? null;
  const fundingKeys = Array.from(
    new Set(result.findings.flatMap((f) => f.intervention?.funding_program_keys ?? [])),
  );

  return (
    <section className="panel overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-5 py-4">
        <Header />
        <OnePagerExport />
      </div>

      <div className="grid gap-3 p-5 md:grid-cols-2">
        {/* The Ask */}
        <Card Icon={Scale} title="The Ask" accent="text-brand" wide>
          {top?.intervention ? (
            <>
              <p className="text-sm font-medium leading-relaxed text-gray-900">
                {top.intervention.name}
                <span className="text-gray-400">
                  {fmtCost(
                    top.intervention.cost_low,
                    top.intervention.cost_high,
                    top.intervention.cost_unit,
                  )}
                </span>
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-gray-400">
                Addresses {top.intervention.trigger.toLowerCase()}
                {top.crash_count_intersection
                  ? `; ${top.crash_count_intersection} crashes documented at this intersection.`
                  : "."}
              </p>
            </>
          ) : (
            <Empty>The specific, costed request renders here once a fix is matched.</Empty>
          )}
        </Card>

        {/* The Money */}
        <Card Icon={Banknote} title="The Money" accent="text-green-700">
          {fundingKeys.length ? (
            <>
              <div className="flex flex-wrap gap-2">
                {fundingKeys.map((k) => (
                  <span
                    key={k}
                    className="rounded-md border border-green-200 bg-green-50 px-2 py-1 font-mono text-[11px] font-semibold text-green-700"
                  >
                    {k}
                  </span>
                ))}
              </div>
              <p className="mt-2.5 text-xs leading-relaxed text-gray-400">
                The city — not the resident — applies. The lever: ask whether this corridor is in
                the city's Action Plan.
              </p>
            </>
          ) : (
            <Empty>Matching grant programs appear here.</Empty>
          )}
        </Card>

        {/* The Messenger */}
        <Card Icon={Megaphone} title="The Messenger" accent="text-sky-600">
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <Building className="h-4 w-4 shrink-0 text-gray-400" />
              City traffic engineer / DOT
            </li>
            <li className="flex items-center gap-2">
              <Users className="h-4 w-4 shrink-0 text-gray-400" />
              District council office
            </li>
            <li className="flex items-center gap-2">
              <Calendar className="h-4 w-4 shrink-0 text-gray-400" />
              Next public meeting where it can be raised
            </li>
          </ul>
          <button className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-sky-600 transition-colors hover:text-gray-900 cursor-pointer">
            Draft a ready-to-send message
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </Card>

        {/* Coalition */}
        <Card Icon={Users} title="Coalition" accent="text-brand">
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold leading-none text-gray-900">
              {result.coalition_count}
            </span>
            <span className="pb-0.5 text-sm text-gray-400">residents flagged this corridor</span>
          </div>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-brand"
              style={{ width: `${Math.min(100, result.coalition_count * 10)}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-gray-400">Political will is a numbers game.</p>
        </Card>

        {/* Accountability */}
        <Card Icon={FileWarning} title="Accountability record" accent="text-red-600" wide>
          {result.accountability.length ? (
            <ol className="relative space-y-3 border-l border-gray-200 pl-4">
              {result.accountability.map((e, i) => {
                const m = ACTION_META[e.action_status];
                return (
                  <li key={i} className="relative">
                    <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-ink-850 bg-slate-500" />
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-[11px] text-gray-400">{e.date}</span>
                      <span className="text-sm font-medium text-gray-900">{e.source}</span>
                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${m.cls}`}
                      >
                        {m.label}
                      </span>
                    </div>
                    <p className="mt-0.5 text-sm leading-relaxed text-gray-400">{e.summary}</p>
                  </li>
                );
              })}
            </ol>
          ) : (
            <Empty>When a corridor was raised — and whether action followed — logs here.</Empty>
          )}
        </Card>
      </div>

      {/* Social post */}
      {result.social_post && (
        <div className="border-t border-gray-100 p-5">
          <p className="eyebrow mb-2 flex items-center gap-1.5 text-gray-400">
            <Megaphone className="h-3.5 w-3.5" />
            Social media post
          </p>
          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
            {result.social_post}
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(result.social_post!)}
            className="btn-ghost mt-2 px-3 py-1.5 text-xs"
          >
            Copy
          </button>
        </div>
      )}

      {/* Council report */}
      {result.council_report && <CouncilReport report={result.council_report} />}

      <p className="border-t border-gray-100 px-5 py-3 text-[11px] leading-relaxed text-gray-400">
        Candidate interventions. Real designs must account for drainage, utilities, ADA, transit,
        and right-of-way not visible in imagery. Confirm with a licensed traffic engineer.
      </p>
    </section>
  );
}

function CouncilReport({ report }: { report: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-t border-gray-100 p-5">
      <div className="flex items-center justify-between">
        <p className="eyebrow flex items-center gap-1.5 text-gray-400">
          <FileWarning className="h-3.5 w-3.5" />
          Formal council report
        </p>
        <div className="flex gap-2">
          <button onClick={() => setOpen(!open)} className="btn-ghost px-3 py-1.5 text-xs">
            {open ? "Hide" : "View"}
          </button>
          <button
            onClick={() => {
              const w = window.open("", "_blank")!;
              w.document.write(`<pre style="font-family:serif;max-width:800px;margin:40px auto;line-height:1.7;white-space:pre-wrap">${report}</pre>`);
              w.document.close();
              w.print();
            }}
            className="btn-primary px-3 py-1.5 text-xs"
          >
            Print / PDF
          </button>
        </div>
      </div>
      {open && (
        <div className="mt-3 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto">
          {report}
        </div>
      )}
    </div>
  );
}

function Header() {
  return (
    <div>
      <p className="eyebrow flex items-center gap-1.5">
        <ArrowRight className="h-3.5 w-3.5 text-brand" />
        The last mile · from finding to funded
      </p>
      <h2 className="mt-1 text-[15px] font-semibold text-gray-900">
        Turn a finding into an action the city is accountable for
      </h2>
    </div>
  );
}

function Card({
  Icon,
  title,
  accent,
  wide,
  children,
}: {
  Icon: typeof Scale;
  title: string;
  accent: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <article
      className={`panel-quiet p-4 transition-colors hover:border-white/15 ${wide ? "md:col-span-2" : ""}`}
    >
      <p className={`eyebrow flex items-center gap-1.5 ${accent}`}>
        <Icon className="h-3.5 w-3.5" />
        {title}
      </p>
      <div className="mt-2.5">{children}</div>
    </article>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm leading-relaxed text-gray-400">{children}</p>;
}
