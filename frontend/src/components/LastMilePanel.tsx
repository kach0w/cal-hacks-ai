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
      <div className="border-b border-[#d4d0c8] px-5 py-4">
        <h2 className="text-base font-bold text-gray-900">Take action</h2>
        <p className="mt-0.5 text-sm text-gray-500">Ready-to-use outputs from the analysis</p>
      </div>

      <div className="grid gap-0 divide-y divide-[#d4d0c8] sm:grid-cols-2 sm:divide-x sm:divide-y-0">
        {/* Social post */}
        <div className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center bg-sky-50 text-sky-600" style={{ borderRadius: 2 }}>
              <Megaphone className="h-3.5 w-3.5" />
            </span>
            <h3 className="text-sm font-bold text-gray-900">Social media post</h3>
          </div>

          {result.social_post ? (
            <>
              <div className="min-h-[140px] border border-[#d4d0c8] bg-[#faf9f6] p-4 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap" style={{ borderRadius: 2 }}>
                {result.social_post}
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(result.social_post!)}
                className="mt-3 inline-flex items-center gap-1.5 border border-[#d4d0c8] bg-white px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
                style={{ borderRadius: 2 }}
              >
                <Copy className="h-3 w-3" />
                Copy to clipboard
              </button>
            </>
          ) : (
            <div className="flex min-h-[140px] items-center justify-center border border-dashed border-[#d4d0c8] text-sm text-gray-400" style={{ borderRadius: 2 }}>
              Generating…
            </div>
          )}
        </div>

        {/* Council report */}
        <div className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center bg-amber-50 text-amber-600" style={{ borderRadius: 2 }}>
              <FileText className="h-3.5 w-3.5" />
            </span>
            <h3 className="text-sm font-bold text-gray-900">Council letter</h3>
          </div>

          {result.council_report ? (
            <CouncilReport report={result.council_report} />
          ) : (
            <div className="flex min-h-[140px] items-center justify-center border border-dashed border-[#d4d0c8] text-sm text-gray-400" style={{ borderRadius: 2 }}>
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

  const paragraphs = report.split(/\n\n+/).filter(Boolean);

  function printReport() {
    const paras = report.split(/\n\n+/).filter(Boolean);
    const html = paras.map(p => `<p>${p.replace(/\n/g, "<br>").replace(/</g, "&lt;").replace(/&lt;br>/g, "<br>")}</p>`).join("\n");
    const w = window.open("", "_blank")!;
    w.document.write(`<!DOCTYPE html><html><head><title>Council Report</title><style>
      body { font-family: Georgia, "Times New Roman", serif; max-width: 680px; margin: 80px auto; line-height: 1.8; color: #111; font-size: 15px; }
      p { margin: 0 0 1.2em 0; }
    </style></head><body>${html}</body></html>`);
    w.document.close();
    w.print();
  }

  return (
    <>
      <div
        className="border border-[#d4d0c8] bg-[#faf9f6] overflow-hidden"
        style={{ borderRadius: 2, maxHeight: open ? "none" : 200, overflow: "hidden", position: "relative" }}
      >
        <div className="p-4" style={{ fontFamily: "Georgia, serif", fontSize: 14, lineHeight: 1.8, color: "#222" }}>
          {paragraphs.map((para, i) => (
            <p key={i} style={{ margin: "0 0 1em 0" }}>{para}</p>
          ))}
        </div>
        {!open && (
          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 48, background: "linear-gradient(to top, #faf9f6, transparent)", pointerEvents: "none" }} />
        )}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-1.5 border border-[#d4d0c8] bg-white px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
          style={{ borderRadius: 2, fontFamily: "Georgia, serif" }}
        >
          {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {open ? "Collapse" : "Read full letter"}
        </button>
        <button
          onClick={printReport}
          className="inline-flex items-center gap-1.5 bg-amber-500 px-3 py-1.5 text-xs text-white hover:bg-amber-600 transition-colors"
          style={{ borderRadius: 2, fontFamily: "Georgia, serif" }}
        >
          <Printer className="h-3 w-3" />
          Export PDF
        </button>
      </div>
    </>
  );
}
