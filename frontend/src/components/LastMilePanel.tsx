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
      <div className="px-5 py-4" style={{ borderBottom: "3px solid #2c3060" }}>
        <h2 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 10, color: "#1a1f3d" }}>▶ TAKE ACTION</h2>
        <p className="mt-1" style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#6070a0" }}>Ready-to-use outputs from the analysis</p>
      </div>

      <div className="grid gap-0 sm:grid-cols-2" style={{ borderColor: "#2c3060", borderTop: "3px solid #2c3060" }}>
        {/* Social post */}
        <div className="p-5" style={{ borderRight: "3px solid #2c3060" }}>
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center" style={{ background: "#daeeff", border: "2px solid #2c3060" }}>
              <Megaphone className="h-3.5 w-3.5" style={{ color: "#3060c8" }} />
            </span>
            <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>SOCIAL POST</h3>
          </div>

          {result.social_post ? (
            <>
              <div className="p-4 whitespace-pre-wrap" style={{ border: "2px solid #2c3060", background: "#e8e4d4", fontFamily: '"VT323", monospace', fontSize: 20, color: "#1a1f3d", lineHeight: 1.5, height: 220, overflowY: "auto" }}>
                {result.social_post}
              </div>
              <button
                onClick={() => navigator.clipboard.writeText(result.social_post!)}
                className="btn-ghost mt-3"
                style={{ fontSize: 8, padding: "8px 12px" }}
              >
                <Copy className="h-3 w-3" />
                COPY
              </button>
            </>
          ) : (
            <div className="flex min-h-[140px] items-center justify-center" style={{ border: "2px dashed #2c3060", fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#6070a0" }}>
              GENERATING…
            </div>
          )}
        </div>

        {/* Council report */}
        <div className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center" style={{ background: "#fff8d0", border: "2px solid #b89000" }}>
              <FileText className="h-3.5 w-3.5" style={{ color: "#b89000" }} />
            </span>
            <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>COUNCIL LETTER</h3>
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
    const html = paras.map(p => `<p>${p.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/\n/g,"<br>")}</p>`).join("\n");
    const w = window.open("", "_blank")!;
    w.document.write(`<!DOCTYPE html><html><head><title>SafeStreets Council Letter</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
  body { background: #e8e4d4; color: #1a1f3d; font-family: "Press Start 2P", monospace; font-size: 11px; line-height: 2; margin: 0; padding: 0; }
  .page { max-width: 680px; margin: 60px auto; padding: 48px; background: #e8e4d4; border: 4px solid #2c3060; box-shadow: 6px 6px 0 #0f1428; }
  .header { font-size: 10px; color: #e8c000; margin-bottom: 28px; border-bottom: 3px solid #2c3060; padding-bottom: 14px; }
  p { margin: 0 0 1.4em 0; }
  @media print {
    body { background: #e8e4d4; }
    .page { border: none; box-shadow: none; margin: 0; padding: 32px; }
  }
</style></head>
<body><div class="page">
<div class="header">▶ SAFESTREETS — COUNCIL LETTER</div>
${html}
</div></body></html>`);
    w.document.close();
    w.print();
  }

  return (
    <>
      <div
        style={{
          border: "2px solid #2c3060",
          background: "#e8e4d4",
          position: "relative",
          height: 220,
          overflow: "hidden",
        }}
      >
        <div className="p-4" style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 11, lineHeight: 2, color: "#1a1f3d" }}>
          {paragraphs.map((para, i) => (
            <p key={i} style={{ margin: "0 0 1.2em 0" }}>{para}</p>
          ))}
        </div>
        {!open && (
          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 60, background: "linear-gradient(to top, #e8e4d4, transparent)", pointerEvents: "none" }} />
        )}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="btn-ghost"
          style={{ fontSize: 8, padding: "8px 12px" }}
        >
          {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {open ? "COLLAPSE" : "READ FULL"}
        </button>
        <button
          onClick={printReport}
          className="btn-primary"
          style={{ fontSize: 8, padding: "8px 12px" }}
        >
          <Printer className="h-3 w-3" />
          Export PDF
        </button>
      </div>
    </>
  );
}
