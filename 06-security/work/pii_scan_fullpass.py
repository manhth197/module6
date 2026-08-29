"""M6-P3003 SECURITY_FULL_PASS — pack-wide secret/PII scan.

Two layers, every hit masked before printing:
  (A) CANONICAL — the exact patterns of .claude/hooks/post_write_secret_scan.ps1 (the repo secret scan the pack
      enforces on every write). This is the authoritative result: what the pack's own gate would flag.
  (B) SUPPLEMENTARY — stricter/defense-in-depth patterns (broad sk-/EAA/etc., 9-19 digit runs, psid literals,
      keyword=value assignments). Expected to surface benign prose false-positives (e.g. 'risk-accept', the word
      'password'); the authoritative signal is layer (A) + the risk-excluded real-token count.
"""
import re, os

ROOT = r"D:\M6\Module6-workspace"
SCAN_ROOTS = [
    os.path.join(ROOT, "04-artifacts"),
    os.path.join(ROOT, "00-spec"),
]
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv", "venv", "_source_snapshot"}
BIN_EXT = {".png",".jpg",".jpeg",".gif",".pdf",".zip",".docx",".xlsx",".pptx",".exe",".dll",".ico",".woff",".woff2",".ttf",".pyc"}

# --- (A) CANONICAL patterns (byte-for-byte from post_write_secret_scan.ps1) ---
TOKEN_SHAPES = {
    "meta token":   re.compile(r"EAA[A-Za-z0-9]{20,}"),
    "openai token": re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "slack token":  re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    "aws key":      re.compile(r"AKIA[0-9A-Z]{16}"),
    "google key":   re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "jwt":          re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}"),
}
SECRET_ASSIGN = re.compile(r"(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|verify[_-]?token|private[_-]?key)\b\s*[:=]\s*['\"]([^'\"\r\n]{12,})['\"]")
SECRET_ALLOWED = re.compile(r"^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)")
IDRX = re.compile(r"(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|member[_-]?id)\b['\"]?\s*[:=]\s*['\"]?(\d{6,})")
EMAILRX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_CONTIG = re.compile(r"(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])")
PHONE_GROUP = re.compile(r"(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)")

# --- (B) SUPPLEMENTARY (stricter / defense-in-depth) ---
SUP_SECRET = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]{6,}|EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,})")
DIGIT_RUN = re.compile(r"(?<![0-9a-fA-F])[0-9]{9,19}(?![0-9a-fA-F])")
PSID_LIT = re.compile(r"(?i)\bpsid\s*[=:]\s*[\"'][^\"']{6,}[\"']")
ASSIGN = re.compile(r"(?i)(password|passwd|client_secret|api_key|apikey|access_token|verify_token|private_key|secret_key|token)\s*[=:]\s*[\"']?([A-Za-z0-9._\-/+]{8,})")
HIGH_ENTROPY = re.compile(r"(EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,}|bearer\s+[A-Za-z0-9._-]{10,})")
HEXCTX = re.compile(r"[0-9a-fA-F]{16,}")

def mask(s):
    s = "".join(ch for ch in s if ch.isprintable())
    return "***" if len(s) <= 6 else f"{s[:3]}***{s[-2:]}"

def preword(line, start):
    j = start
    while j > 0 and (line[j-1].isalnum() or line[j-1] in "-_"): j -= 1
    return line[j:start+3]

def iter_files():
    for base in SCAN_ROOTS:
        for dp, dns, fns in os.walk(base):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in fns:
                if os.path.splitext(fn)[1].lower() in BIN_EXT: continue
                yield os.path.join(dp, fn)

canon = {"token": [], "secret_assign": [], "user_id": [], "email": [], "phone": []}
sup = {"SUP_SECRET": [], "DIGIT_RUN": [], "PSID_LIT": []}
real_assign, real_token = [], []
files = 0
for fp in iter_files():
    try:
        text = open(fp, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print("  !! cannot read", fp, e); continue
    files += 1
    rel = os.path.relpath(fp, ROOT)
    lines = text.splitlines()
    # (A) canonical — whole-file matches
    for name, rx in TOKEN_SHAPES.items():
        for m in rx.finditer(text): canon["token"].append((rel, name, mask(m.group(0))))
    for m in SECRET_ASSIGN.finditer(text):
        val = m.group(2)
        if not SECRET_ALLOWED.match(val):
            canon["secret_assign"].append((rel, m.group(1), mask(val)))
    for m in IDRX.finditer(text): canon["user_id"].append((rel, m.group(1), mask(m.group(2))))
    for m in EMAILRX.finditer(text): canon["email"].append((rel, mask(m.group(0))))
    for m in PHONE_CONTIG.finditer(text): canon["phone"].append((rel, "contig", mask(m.group(0))))
    for m in PHONE_GROUP.finditer(text): canon["phone"].append((rel, "grouped", mask(m.group(0))))
    # (B) supplementary — per line (for hex-context + risk-word exclusion)
    for i, line in enumerate(lines, 1):
        for m in SUP_SECRET.finditer(line): sup["SUP_SECRET"].append((rel, i, mask(m.group(0))))
        for m in DIGIT_RUN.finditer(line):
            note = ""
            for hm in HEXCTX.finditer(line):
                if hm.start() <= m.start() and hm.end() >= m.end(): note = "HEXCTX"; break
            sup["DIGIT_RUN"].append((rel, i, mask(m.group(0)), note))
        for m in PSID_LIT.finditer(line): sup["PSID_LIT"].append((rel, i, mask(m.group(0))))
        for m in ASSIGN.finditer(line):
            v = m.group(2)
            if v.lower() in ("value","none","null","xxx","masked","secret_ref","abc","the","that","only","required","string","false","true"): continue
            real_assign.append((rel, i, m.group(1), mask(v)))
        for m in HIGH_ENTROPY.finditer(line):
            tok = m.group(0)
            if tok.lower().startswith("sk-") and preword(line, m.start()).lower().startswith("ri"): continue
            real_token.append((rel, i, mask(tok), preword(line, m.start())))

print(f"=== FILES SCANNED: {files} ===")
print("\n===== (A) CANONICAL repo secret scan (post_write_secret_scan patterns) =====")
print(f"  token shapes:        {len(canon['token'])}")
for r in canon["token"][:20]: print("    ", r)
print(f"  secret assignments:  {len(canon['secret_assign'])}")
for r in canon["secret_assign"][:20]: print("    ", r)
print(f"  raw user-id assigns: {len(canon['user_id'])}")
for r in canon["user_id"][:20]: print("    ", r)
print(f"  emails:              {len(canon['email'])}")
for r in canon["email"][:20]: print("    ", r)
print(f"  phones:              {len(canon['phone'])}")
for r in canon["phone"][:20]: print("    ", r)
print("\n===== (B) SUPPLEMENTARY (stricter; expect benign prose FPs) =====")
print(f"  SUP_SECRET (broad sk-/EAA/...): {len(sup['SUP_SECRET'])}")
for r in sup["SUP_SECRET"][:8]: print("    ", r)
if len(sup["SUP_SECRET"])>8: print(f"     ... +{len(sup['SUP_SECRET'])-8} more (broad sk- matches 'risk-*' prose)")
print(f"  DIGIT_RUN 9-19 (non-hex): {len(sup['DIGIT_RUN'])}")
for r in sup["DIGIT_RUN"][:20]: print("    ", r)
if len(sup["DIGIT_RUN"])>20: print(f"     ... +{len(sup['DIGIT_RUN'])-20} more")
print(f"  PSID literals: {len(sup['PSID_LIT'])}")
for r in sup["PSID_LIT"][:20]: print("    ", r)
print("\n===== AUTHORITATIVE DISCRIMINATORS =====")
print(f"  REAL keyword=VALUE credential assignments: {len(real_assign)}")
for r in real_assign[:40]: print("    ", r)
print(f"  REAL high-entropy tokens (risk-* excluded): {len(real_token)}")
for r in real_token[:40]: print("    ", r)
