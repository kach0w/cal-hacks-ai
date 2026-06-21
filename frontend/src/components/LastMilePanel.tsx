import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import { Megaphone, FileText, Copy, Printer, ChevronDown, ChevronUp } from "./icons";

export default function LastMilePanel({ lat, lng }: { lat: number; lng: number }) {
  const { result, loading } = useIntersection(lat, lng);

  if (loading || !result) {
    return (
      <section className="panel p-6">
        <div className="mb-5 h-5 w-40 animate-pulse rounded bg-gray-100" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-48 animate-pulse rounded-2xl bg-gray-100" />
          <div className="h-48 animate-pulse rounded-2xl bg-gray-100" />
        </div>
      </section>
    );
  }

  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-gray-100 px-6 py-5">
        <h2 className="text-base font-semibold text-gray-900">Take action</h2>
        <p className="mt-0.5 text-sm text-gray-400">Ready-to-use outputs from the analysis</p>
      </div>

      <div className="grid gap-0 divide-y divide-gray-100 sm:grid-cols-2 sm:divide-x sm:divide-y-0">
        {/* Social post */}
        <div className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-sky-50 text-sky-500">
              <Megaphone className="h-4 w-4" />
            </span>
            <h3 className="text-sm font-semibold text-gray-900">Social media post</h3>
          </div>

          {result.social_post ? (
            <>
              <div className="min-h-[140px] rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
                {result.social_post}
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(result.social_post!)}
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-600 shadow-sm hover:bg-gray-50 transition-colors"
              >
                <Copy className="h-3.5 w-3.5" />
                Copy to clipboard
              </button>
            </>
          ) : (
            <div className="flex min-h-[140px] items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-400">
              Generating…
            </div>
          )}
        </div>

        {/* Council report */}
        <div className="p-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-amber-50 text-amber-500">
              <FileText className="h-4 w-4" />
            </span>
            <h3 className="text-sm font-semibold text-gray-900">Council report</h3>
          </div>

          {result.council_report ? (
            <CouncilReport report={result.council_report} />
          ) : (
            <div className="flex min-h-[140px] items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-400">
              Generating…
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function CouncilReport({ report }: { report: string }) {
  const [open, setOpen] = useState(false);

  function printReport() {
    const w = window.open("", "_blank")!;
    w.document.write(`<!DOCTYPE html><html><head><title>Council Report</title><style>
      body { font-family: Georgia, serif; max-width: 760px; margin: 60px auto; line-height: 1.8; color: #111; font-size: 15px; }
      pre { white-space: pre-wrap; font-family: inherit; }
    </style></head><body><pre>${report.replace(/</g, "&lt;")}</pre></body></html>`);
    w.document.close();
    w.print();
  }

  return (
    <>
      <div className="min-h-[140px] overflow-hidden rounded-xl border border-gray-200 bg-gray-50">
        <div
          className={`p-4 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap transition-all ${open ? "" : "line-clamp-5"}`}
        >
          {report}
        </div>
        {!open && (
          <div className="bg-gradient-to-t from-gray-50 to-transparent h-8 -mt-8 relative pointer-events-none" />
        )}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-600 shadow-sm hover:bg-gray-50 transition-colors"
        >
          {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {open ? "Collapse" : "Read full"}
        </button>
        <button
          onClick={printReport}
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-2 text-xs font-medium text-white shadow-sm hover:bg-amber-400 transition-colors"
        >
          <Printer className="h-3.5 w-3.5" />
          Export PDF
        </button>
      </div>
    </>
  );
}
