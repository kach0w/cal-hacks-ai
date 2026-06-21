"""A tiny, dependency-free PDF writer for the council letter attachment.

We only need crisp wrapped text on US-Letter pages, so we emit a minimal PDF that uses the
built-in Helvetica (one of the 14 standard fonts — no embedding required). This avoids
pulling in reportlab/weasyprint just to attach a letter to an email.
"""
from __future__ import annotations

import textwrap

_PAGE_W, _PAGE_H = 612, 792          # US Letter, points
_MARGIN = 72
_FONT_SIZE = 11
_LEADING = 16
_TITLE_SIZE = 15
# Helvetica's average glyph is ~0.5em wide; size the wrap conservatively from that.
_USABLE_W = _PAGE_W - 2 * _MARGIN
_CHARS_PER_LINE = int(_USABLE_W / (_FONT_SIZE * 0.5))
_TOP_Y = _PAGE_H - _MARGIN
_LINES_PER_PAGE = int((_PAGE_H - 2 * _MARGIN) / _LEADING) - 1


def _esc(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _wrap(text: str) -> list[str]:
    """Word-wrap the letter, preserving blank lines between paragraphs."""
    out: list[str] = []
    for raw in text.split("\n"):
        if not raw.strip():
            out.append("")
            continue
        out.extend(textwrap.wrap(raw, width=_CHARS_PER_LINE) or [""])
    return out


def _paginate(lines: list[str]) -> list[list[str]]:
    return [lines[i : i + _LINES_PER_PAGE] for i in range(0, len(lines), _LINES_PER_PAGE)] or [[]]


def _content_stream(lines: list[str], title: str | None) -> bytes:
    parts = ["BT", f"{_MARGIN} {_TOP_Y} Td", f"{_LEADING} TL"]
    if title:
        parts += [f"/F1 {_TITLE_SIZE} Tf", f"({_esc(title)}) Tj", "T*", "T*", f"/F1 {_FONT_SIZE} Tf"]
    else:
        parts.append(f"/F1 {_FONT_SIZE} Tf")
    for ln in lines:
        parts.append(f"({_esc(ln)}) Tj" if ln else "")
        parts.append("T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", "replace")


def council_letter_pdf(title: str, body: str) -> bytes:
    """Render `title` + `body` to a multi-page Helvetica PDF and return the bytes."""
    pages = _paginate(_wrap(body))

    objects: list[bytes] = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)  # 1-based object number

    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Reserve the Pages object number (filled once we know the kids).
    objects.append(b"")          # placeholder for Pages
    pages_id = len(objects)

    page_ids: list[int] = []
    for i, page_lines in enumerate(pages):
        stream = _content_stream(page_lines, title if i == 0 else None)
        content_id = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        page_id = add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
            % (pages_id, _PAGE_W, _PAGE_H, font_id, content_id)
        )
        page_ids.append(page_id)

    kids = b" ".join(b"%d 0 R" % pid for pid in page_ids)
    objects[pages_id - 1] = b"<< /Type /Pages /Count %d /Kids [%s] >>" % (len(page_ids), kids)

    catalog_id = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)

    # Assemble the file with a byte-accurate xref table.
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for n, body_bytes in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body_bytes + b"\nendobj\n"

    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (
        b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF"
        % (len(objects) + 1, catalog_id, xref_pos)
    )
    return bytes(out)
