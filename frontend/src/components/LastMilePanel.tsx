import { useState } from "react";
import { useIntersection } from "../hooks/useIntersection";
import { composeCouncilEmail } from "../api/client";
import type { CouncilEmailDraft } from "../types";
import type { RedditPost } from "../types";
import { Megaphone, FileText, Copy, Printer, ChevronDown, ChevronUp, Retweet, Heart, Mail, Paperclip, Download, Reddit, ArrowUp, MessageSquare } from "./icons";

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
        {/* Social post — tweet card */}
        <div className="p-5" style={{ borderRight: "3px solid #2c3060" }}>
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center" style={{ background: "#daeeff", border: "2px solid #2c3060" }}>
              <Megaphone className="h-3.5 w-3.5" style={{ color: "#3060c8" }} />
            </span>
            <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>TWEET</h3>
          </div>

          {result.social_post ? (
            <TweetCard text={result.social_post} />
          ) : (
            <div className="flex items-center justify-center" style={{ border: "2px dashed #2c3060", height: 300, fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#6070a0" }}>
              GENERATING…
            </div>
          )}

          {/* Reddit post — posts to the street's local subreddit */}
          <div className="mt-5 mb-3 flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center" style={{ background: "#ffe2d4", border: "2px solid #b03000" }}>
              <Reddit className="h-3.5 w-3.5" style={{ color: "#ff4500" }} />
            </span>
            <h3 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>REDDIT</h3>
          </div>

          {result.reddit_post ? (
            <RedditCard post={result.reddit_post} />
          ) : (
            <div className="flex items-center justify-center" style={{ border: "2px dashed #2c3060", height: 300, fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#6070a0" }}>
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
            <CouncilReport report={result.council_report} lat={lat} lng={lng} />
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

function CouncilReport({ report, lat, lng }: { report: string; lat: number; lng: number }) {
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
          height: 300,
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

      <EmailCouncil lat={lat} lng={lng} />
    </>
  );
}

/**
 * Email-the-council action that sits under the printable report. An LLM email agent on the
 * backend writes a human, professional message (concerns + statistics + call to action) and
 * a subject line, resolves the council member(s) by jurisdiction (Socrata), and returns the
 * draft plus the report PDF. The user can send it through whichever platform they use:
 * desktop mail (a .eml that opens with the PDF already attached) or web Gmail/Outlook/default
 * (a prefilled compose window — web compose can't carry an attachment, so we download the PDF
 * for them to attach in one click).
 */
function downloadBase64(b64: string, name: string, mime: string) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

type WebPlatform = "gmail" | "outlook" | "mailto";

function composeUrl(platform: WebPlatform, to: string, subject: string, body: string): string {
  const s = encodeURIComponent(subject);
  const b = encodeURIComponent(body);
  switch (platform) {
    case "gmail":
      return `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${s}&body=${b}`;
    case "outlook":
      return `https://outlook.office.com/mail/deeplink/compose?to=${encodeURIComponent(to)}&subject=${s}&body=${b}`;
    case "mailto":
      return `mailto:${to}?subject=${s}&body=${b}`;
  }
}

function EmailCouncil({ lat, lng }: { lat: number; lng: number }) {
  const [draft, setDraft] = useState<CouncilEmailDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [attachHint, setAttachHint] = useState(false);

  async function compose() {
    setLoading(true);
    setError(false);
    const d = await composeCouncilEmail(lat, lng);
    if (d) setDraft(d);
    else setError(true);
    setLoading(false);
  }

  /** Web compose (Gmail/Outlook/default): prefill the message and hand over the PDF to attach. */
  function sendVia(platform: WebPlatform) {
    if (!draft) return;
    const to = draft.recipients.map((r) => r.email).join(",");
    downloadBase64(draft.pdf_base64, draft.pdf_filename, "application/pdf");
    window.open(composeUrl(platform, to, draft.subject, draft.body), "_blank");
    setAttachHint(true);
  }

  /** Desktop mail: a .eml that opens in Outlook/Apple Mail with the PDF already attached. */
  function downloadEml() {
    if (!draft) return;
    downloadBase64(draft.eml_base64, draft.filename, "message/rfc822");
  }

  return (
    <div className="mt-4" style={{ borderTop: "2px dashed #2c3060", paddingTop: 14 }}>
      <div className="mb-2 flex items-center gap-2">
        <span className="grid h-6 w-6 place-items-center" style={{ background: "#daeeff", border: "2px solid #2c3060" }}>
          <Mail className="h-3 w-3" style={{ color: "#3060c8" }} />
        </span>
        <h4 style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#1a1f3d" }}>EMAIL CITY COUNCIL</h4>
      </div>

      {!draft && (
        <>
          <p style={{ fontFamily: '"VT323", monospace', fontSize: 16, color: "#6070a0", margin: "0 0 8px" }}>
            An email agent drafts a professional message to the councilmember for this
            intersection — with the report PDF attached.
          </p>
          <button
            onClick={compose}
            disabled={loading}
            className="btn-primary"
            style={{ fontSize: 8, padding: "8px 12px", opacity: loading ? 0.6 : 1 }}
          >
            <Mail className="h-3 w-3" />
            {loading ? "DRAFTING…" : "Draft email to council"}
          </button>
          {error && (
            <p style={{ fontFamily: '"VT323", monospace', fontSize: 16, color: "#e84040", margin: "8px 0 0" }}>
              Couldn't draft the email — run the analysis for this intersection first, then retry.
            </p>
          )}
        </>
      )}

      {draft && (
        <div style={{ border: "2px solid #2c3060", background: "#e8e4d4" }}>
          <div style={{ padding: "8px 10px", borderBottom: "2px solid #2c3060" }}>
            <FieldRow label="TO">
              {draft.recipients.map((r, i) => (
                <span key={i} title={r.role + (r.district ? ` · District ${r.district}` : "")} style={{ display: "inline-block", marginRight: 6, marginBottom: 4, padding: "2px 6px", background: "#daeeff", border: "2px solid #3060c8", fontFamily: '"VT323", monospace', fontSize: 15, color: "#1a1f3d" }}>
                  {r.email}
                </span>
              ))}
            </FieldRow>
            <FieldRow label="SUBJECT">
              <span style={{ fontFamily: '"VT323", monospace', fontSize: 17, color: "#1a1f3d" }}>{draft.subject}</span>
            </FieldRow>
          </div>

          <div style={{ padding: "10px", maxHeight: 180, overflowY: "auto", fontFamily: '"VT323", monospace', fontSize: 17, lineHeight: 1.4, color: "#1a1f3d", whiteSpace: "pre-wrap" }}>
            {draft.body}
          </div>

          <div style={{ padding: "8px 10px", borderTop: "2px solid #2c3060" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 8, fontFamily: '"VT323", monospace', fontSize: 15, color: "#6070a0" }}>
              <Paperclip className="h-3 w-3" />
              {draft.pdf_filename}
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              <button onClick={() => sendVia("gmail")} className="btn-primary" style={{ fontSize: 8, padding: "8px 10px" }}>
                <Mail className="h-3 w-3" />
                Gmail
              </button>
              <button onClick={() => sendVia("outlook")} className="btn-primary" style={{ fontSize: 8, padding: "8px 10px" }}>
                <Mail className="h-3 w-3" />
                Outlook
              </button>
              <button onClick={() => sendVia("mailto")} className="btn-ghost" style={{ fontSize: 8, padding: "8px 10px" }}>
                <Mail className="h-3 w-3" />
                Default app
              </button>
              <button onClick={downloadEml} className="btn-ghost" style={{ fontSize: 8, padding: "8px 10px" }}>
                <Download className="h-3 w-3" />
                .eml (Outlook/Apple — PDF attached)
              </button>
            </div>

            <p style={{ fontFamily: '"VT323", monospace', fontSize: 15, lineHeight: 1.3, color: attachHint ? "#1a1f3d" : "#6070a0", margin: "8px 0 0" }}>
              {attachHint
                ? `↳ Your draft opened in a new tab and ${draft.pdf_filename} downloaded — attach it before sending.`
                : "Gmail / Outlook / Default open a prefilled draft (the PDF downloads to attach). The .eml opens in a desktop mail app with the PDF already attached."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "baseline", marginBottom: 4 }}>
      <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", flexShrink: 0, width: 56 }}>{label}</span>
      <span style={{ flex: 1 }}>{children}</span>
    </div>
  );
}

function TweetCard({ text }: { text: string }) {
  const [retweeted, setRetweeted] = useState(false);
  const [liked, setLiked] = useState(false);
  const [rtCount, setRtCount] = useState(47);
  const [likeCount, setLikeCount] = useState(112);

  function handleRetweet() {
    setRetweeted(!retweeted);
    setRtCount(c => retweeted ? c - 1 : c + 1);
  }
  function handleLike() {
    setLiked(!liked);
    setLikeCount(c => liked ? c - 1 : c + 1);
  }
  function handleShare() {
    const encoded = encodeURIComponent(text);
    window.open(`https://twitter.com/intent/tweet?text=${encoded}`, "_blank");
  }

  return (
    <div style={{ border: "3px solid #2c3060", background: "#e8e4d4", height: 300, display: "flex", flexDirection: "column" }}>
      {/* Tweet header */}
      <div style={{ padding: "12px 14px 8px", borderBottom: "2px solid #2c3060", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 36, height: 36, background: "#1a1f3d", border: "2px solid #2c3060", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <span style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 8, color: "#e8c000" }}>SS</span>
        </div>
        <div>
          <div style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#1a1f3d" }}>SafeStreets</div>
          <div style={{ fontFamily: '"VT323", monospace', fontSize: 15, color: "#6070a0" }}>@safestreets_ai</div>
        </div>
        <div style={{ marginLeft: "auto", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#3060c8", background: "#daeeff", border: "2px solid #3060c8", padding: "3px 8px" }}>
          𝕏
        </div>
      </div>

      {/* Tweet body */}
      <div style={{ flex: 1, padding: "12px 14px", overflowY: "auto", fontFamily: '"VT323", monospace', fontSize: 20, color: "#1a1f3d", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
        {text}
      </div>

      {/* Tweet actions */}
      <div style={{ borderTop: "2px solid #2c3060", padding: "8px 14px", display: "flex", alignItems: "center", gap: 6 }}>
        <button
          onClick={handleRetweet}
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "pointer", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: retweeted ? "#38a832" : "#6070a0", padding: "4px 6px" }}
        >
          <Retweet className="h-3 w-3" />
          {rtCount}
        </button>
        <button
          onClick={handleLike}
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "pointer", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: liked ? "#e84040" : "#6070a0", padding: "4px 6px" }}
        >
          <Heart className="h-3 w-3" />
          {likeCount}
        </button>
        <button
          onClick={() => navigator.clipboard.writeText(text)}
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "pointer", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", padding: "4px 6px" }}
        >
          <Copy className="h-3 w-3" />
          COPY
        </button>
        <button
          onClick={handleShare}
          className="btn-primary"
          style={{ marginLeft: "auto", fontSize: 7, padding: "5px 10px" }}
        >
          POST →
        </button>
      </div>
    </div>
  );
}

/**
 * Reddit card for the street's local subreddit. The subreddit is resolved on the backend
 * from the intersection's city, and the title/body are written by the agent to read like a
 * real concerned neighbor's post (not AI). POST opens Reddit's submit page prefilled.
 */
function RedditCard({ post }: { post: RedditPost }) {
  const [upvoted, setUpvoted] = useState(false);
  const [score, setScore] = useState(128);

  function handleUpvote() {
    setUpvoted(!upvoted);
    setScore(c => (upvoted ? c - 1 : c + 1));
  }
  function handlePost() {
    const url = `https://www.reddit.com/r/${post.subreddit}/submit?title=${encodeURIComponent(post.title)}&text=${encodeURIComponent(post.body)}`;
    window.open(url, "_blank");
  }
  function handleCopy() {
    navigator.clipboard.writeText(`${post.title}\n\n${post.body}`);
  }

  return (
    <div style={{ border: "3px solid #2c3060", background: "#e8e4d4", height: 300, display: "flex", flexDirection: "column" }}>
      {/* Reddit header */}
      <div style={{ padding: "12px 14px 8px", borderBottom: "2px solid #2c3060", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 36, height: 36, background: "#ff4500", border: "2px solid #2c3060", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Reddit className="h-5 w-5" style={{ color: "#fff" }} />
        </div>
        <div>
          <div style={{ fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#1a1f3d" }}>r/{post.subreddit}</div>
          <div style={{ fontFamily: '"VT323", monospace', fontSize: 15, color: "#6070a0" }}>Posted by u/safestreets_ai</div>
        </div>
        <div style={{ marginLeft: "auto", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#ff4500", background: "#ffe2d4", border: "2px solid #ff4500", padding: "3px 8px" }}>
          ⤴
        </div>
      </div>

      {/* Reddit body */}
      <div style={{ flex: 1, padding: "12px 14px", overflowY: "auto" }}>
        <div style={{ fontFamily: '"VT323", monospace', fontSize: 22, fontWeight: "bold", color: "#1a1f3d", lineHeight: 1.2, marginBottom: 8 }}>
          {post.title}
        </div>
        <div style={{ fontFamily: '"VT323", monospace', fontSize: 18, color: "#1a1f3d", lineHeight: 1.4, whiteSpace: "pre-wrap" }}>
          {post.body}
        </div>
      </div>

      {/* Reddit actions */}
      <div style={{ borderTop: "2px solid #2c3060", padding: "8px 14px", display: "flex", alignItems: "center", gap: 6 }}>
        <button
          onClick={handleUpvote}
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "pointer", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: upvoted ? "#ff4500" : "#6070a0", padding: "4px 6px" }}
        >
          <ArrowUp className="h-3 w-3" />
          {score}
        </button>
        <button
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "default", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", padding: "4px 6px" }}
        >
          <MessageSquare className="h-3 w-3" />
          24
        </button>
        <button
          onClick={handleCopy}
          style={{ display: "flex", alignItems: "center", gap: 5, background: "none", border: "none", cursor: "pointer", fontFamily: '"Press Start 2P", monospace', fontSize: 7, color: "#6070a0", padding: "4px 6px" }}
        >
          <Copy className="h-3 w-3" />
          COPY
        </button>
        <button
          onClick={handlePost}
          className="btn-primary"
          style={{ marginLeft: "auto", fontSize: 7, padding: "5px 10px" }}
        >
          POST →
        </button>
      </div>
    </div>
  );
}
