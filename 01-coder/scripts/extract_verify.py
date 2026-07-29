#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_verify.py — deterministic Phase-A extraction coverage check.

Independently re-parses word/document.xml (NOT reusing docx_extract.py's
walker) and asserts that every non-empty paragraph and table-cell text block
appears, in document order, inside the extract markdown. Whitespace is
normalized; markdown syntax is stripped from the extract before comparison.

Exit 0 = full coverage in order. Exit 2 = deviations (printed as JSON).
Usage: .venv\\Scripts\\python.exe extract_verify.py <input.docx> <extract.md>
"""
import sys, json, zipfile, re, unicodedata
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = s.replace(" ", " ").replace("​", "")
    return re.sub(r"\s+", " ", s).strip()

def blocks_from_docx(path):
    """Yield every logical text block (paragraph / table cell paragraph) in order."""
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    out = []
    def para_text(p):
        parts = []
        for n in p.iter():
            if n.tag == W + "t":
                parts.append(n.text or "")
            elif n.tag == W + "tab":
                parts.append(" ")
            elif n.tag in (W + "br", W + "cr"):
                parts.append(" ")
        return norm("".join(parts))
    def walk(el):
        for child in el:
            if child.tag == W + "p":
                t = para_text(child)
                if t:
                    out.append(t)
            elif child.tag == W + "tbl":
                for tr in child.findall(W + "tr"):
                    for tc in tr.findall(W + "tc"):
                        walk(tc)
    walk(body)
    return out

def flatten_extract(path):
    """Strip ONLY markdown syntax the extractor itself introduced (heading
    hashes, table pipes/separator rows, <br>, [IMAGE]/nested-table markers).
    Literal document text — including inline pipes in enum values and literal
    leading dashes — is left untouched."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    out = []
    for line in lines:
        line = line.replace("<br>", " ")
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            out.append(m.group(1))
            continue
        s = line.strip()
        if re.match(r"^\|(?:-{3,}\|)+$", s):
            continue  # markdown table separator row
        if s.startswith("**[NESTED TABLE") or s == "[IMAGE]":
            continue
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            # table row emitted by the extractor: unescape, drop cell pipes
            body = s[1:-1].replace("\\|", "\x00")
            cells = [c.strip().replace("\x00", "|") for c in body.split("|")]
            out.append(" ".join(cells))
            continue
        out.append(line.replace("[IMAGE]", " "))
    return norm("\n".join(out))

def main():
    docx, extract = sys.argv[1], sys.argv[2]
    blocks = blocks_from_docx(docx)
    hay = flatten_extract(extract)
    missing, out_of_order = [], []
    cursor = 0
    for i, b in enumerate(blocks):
        pos = hay.find(b, cursor)
        if pos >= 0:
            cursor = pos + len(b)
            continue
        pos_any = hay.find(b)
        if pos_any >= 0:
            out_of_order.append({"index": i, "text": b[:120]})
            # do not advance cursor; tolerate local reordering of table emission
        else:
            missing.append({"index": i, "text": b[:200]})
    result = {
        "source_blocks": len(blocks),
        "missing": missing,
        "out_of_order": out_of_order,
        "verdict": "FAITHFUL" if not missing and not out_of_order else "DEVIATION",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["verdict"] == "FAITHFUL" else 2)

if __name__ == "__main__":
    main()
