#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_extract.py — stdlib-only faithful .docx -> markdown/text extractor.

Used ONCE in Phase A to produce the canonical extract of the owner
specification. Preserves: headings (style-based), paragraph text verbatim,
list numbering (rendered from numbering.xml where auto-numbered), tables
row-by-row (nested tables flattened with markers), tabs, line breaks.

Outputs:
  1) <out>.md        — structured markdown extract
  2) <out>.rawdump.txt — one logical block per line (P####: / T##R##C##:)
     for adversarial verification against the source.
  3) prints a JSON summary (counts, sha256 of the source docx).

Usage: .venv\\Scripts\\python.exe docx_extract.py <input.docx> <out_basename>
"""
import sys, io, json, zipfile, hashlib, re
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def qn(tag):
    return W + tag

def get_text_of_para(p):
    """Concatenate all runs of a paragraph, preserving tabs and breaks."""
    parts = []
    for node in p.iter():
        tag = node.tag
        if tag == qn("t"):
            parts.append(node.text or "")
        elif tag == qn("tab"):
            parts.append("\t")
        elif tag == qn("br") or tag == qn("cr"):
            parts.append("\n")
        elif tag == qn("noBreakHyphen"):
            parts.append("-")
    return "".join(parts)

def para_style(p, styles_map):
    pPr = p.find(qn("pPr"))
    if pPr is None:
        return None
    s = pPr.find(qn("pStyle"))
    if s is None:
        return None
    sid = s.get(qn("val"))
    return styles_map.get(sid, sid)

def para_numbering(p):
    """Return (numId, ilvl) or None."""
    pPr = p.find(qn("pPr"))
    if pPr is None:
        return None
    numPr = pPr.find(qn("numPr"))
    if numPr is None:
        return None
    numId = numPr.find(qn("numId"))
    ilvl = numPr.find(qn("ilvl"))
    if numId is None:
        return None
    try:
        return (numId.get(qn("val")), int(ilvl.get(qn("val"))) if ilvl is not None else 0)
    except (TypeError, ValueError):
        return None

def load_styles(z):
    """styleId -> style name (e.g. 'heading 1')."""
    m = {}
    try:
        root = ET.fromstring(z.read("word/styles.xml"))
    except KeyError:
        return m
    for st in root.findall(qn("style")):
        sid = st.get(qn("styleId"))
        nm = st.find(qn("name"))
        if sid and nm is not None:
            m[sid] = nm.get(qn("val"), sid)
    return m

def load_numbering(z):
    """numId -> {ilvl: (numFmt, lvlText)}. Best-effort; used to render list markers."""
    result = {}
    try:
        root = ET.fromstring(z.read("word/numbering.xml"))
    except KeyError:
        return result
    abstract = {}
    for a in root.findall(qn("abstractNum")):
        aid = a.get(qn("abstractNumId"))
        lvls = {}
        for lvl in a.findall(qn("lvl")):
            i = int(lvl.get(qn("ilvl"), "0"))
            fmt_el = lvl.find(qn("numFmt"))
            txt_el = lvl.find(qn("lvlText"))
            fmt = fmt_el.get(qn("val")) if fmt_el is not None else "bullet"
            txt = txt_el.get(qn("val")) if txt_el is not None else ""
            lvls[i] = (fmt, txt)
        abstract[aid] = lvls
    for n in root.findall(qn("num")):
        nid = n.get(qn("numId"))
        ref = n.find(qn("abstractNumId"))
        if ref is not None:
            result[nid] = abstract.get(ref.get(qn("val")), {})
    return result

HEADING_RE = re.compile(r"^heading\s*(\d)$", re.I)

class Extractor:
    def __init__(self, z):
        self.z = z
        self.styles = load_styles(z)
        self.numbering = load_numbering(z)
        self.md = []          # markdown lines
        self.raw = []         # raw dump lines
        self.counters = {}    # (numId, ilvl) -> current count
        self.pcount = 0
        self.tcount = 0
        self.img_count = 0
        self.heading_count = 0

    def esc_cell(self, s):
        return s.replace("|", "\\|").replace("\n", "<br>")

    def emit_para(self, p, in_table=False):
        text = get_text_of_para(p)
        for node in p.iter():
            if node.tag.endswith("}drawing") or node.tag.endswith("}pict"):
                self.img_count += 1
                text += " [IMAGE]"
        if in_table:
            return text
        self.pcount += 1
        stripped = text.strip()
        style = para_style(p, self.styles) or ""
        m = HEADING_RE.match(style.strip())
        if stripped:
            self.raw.append("P%04d: %s" % (self.pcount, stripped.replace("\n", " / ")))
        if m and stripped:
            level = int(m.group(1))
            self.heading_count += 1
            self.md.append("")
            self.md.append("#" * min(level + 1, 6) + " " + stripped)
            self.md.append("")
            return None
        num = para_numbering(p)
        if num and stripped:
            numId, ilvl = num
            fmtinfo = self.numbering.get(numId, {}).get(ilvl, ("bullet", ""))
            indent = "  " * ilvl
            if fmtinfo[0] == "bullet":
                self.md.append("%s- %s" % (indent, stripped))
            else:
                key = (numId, ilvl)
                self.counters[key] = self.counters.get(key, 0) + 1
                # reset deeper levels
                for k in list(self.counters):
                    if k[0] == numId and k[1] > ilvl:
                        del self.counters[k]
                self.md.append("%s%d. %s" % (indent, self.counters[key], stripped))
        elif stripped:
            self.md.append(stripped)
            self.md.append("")
        return None

    def emit_table(self, tbl, nested=False):
        self.tcount += 1
        tid = self.tcount
        rows = tbl.findall(qn("tr"))
        self.md.append("")
        if nested:
            self.md.append("**[NESTED TABLE T%02d]**" % tid)
        md_rows = []
        for r_i, tr in enumerate(rows, 1):
            cells = tr.findall(qn("tc"))
            cell_texts = []
            for c_i, tc in enumerate(cells, 1):
                parts = []
                for child in tc:
                    if child.tag == qn("p"):
                        t = self.emit_para(child, in_table=True)
                        if t is not None and t.strip():
                            parts.append(t.strip())
                    elif child.tag == qn("tbl"):
                        parts.append("[NESTED-TABLE-BELOW]")
                        self._pending_nested = getattr(self, "_pending_nested", [])
                        self._pending_nested.append(child)
                cell = " / ".join(parts)
                cell_texts.append(cell)
                if cell.strip():
                    self.raw.append("T%02dR%02dC%02d: %s" % (tid, r_i, c_i, cell.replace("\n", " / ")))
            md_rows.append(cell_texts)
        width = max((len(r) for r in md_rows), default=0)
        for i, r in enumerate(md_rows):
            r += [""] * (width - len(r))
            self.md.append("| " + " | ".join(self.esc_cell(c) for c in r) + " |")
            if i == 0:
                self.md.append("|" + "---|" * width)
        self.md.append("")
        for nt in getattr(self, "_pending_nested", []):
            self.emit_table(nt, nested=True)
        self._pending_nested = []

    def run(self):
        root = ET.fromstring(self.z.read("word/document.xml"))
        body = root.find(qn("body"))
        for child in body:
            if child.tag == qn("p"):
                self.emit_para(child)
            elif child.tag == qn("tbl"):
                self.emit_table(child)

def main():
    src, out = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with zipfile.ZipFile(src) as z:
        ex = Extractor(z)
        ex.run()
        extra = [n for n in z.namelist() if re.search(r"word/(comments|footnotes|endnotes)\.xml$", n)]
    md_text = "\n".join(ex.md)
    md_text = re.sub(r"\n{3,}", "\n\n", md_text)
    with io.open(out + ".md", "w", encoding="utf-8", newline="\n") as f:
        f.write(md_text + "\n")
    with io.open(out + ".rawdump.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(ex.raw) + "\n")
    print(json.dumps({
        "source": src, "sha256": digest,
        "paragraphs": ex.pcount, "tables": ex.tcount,
        "headings": ex.heading_count, "images": ex.img_count,
        "extra_parts_present": extra,
        "md_lines": md_text.count("\n") + 1,
        "raw_lines": len(ex.raw),
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
