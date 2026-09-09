"""M6-P2506 SECURITY_PII independent scan (slice M6.2Q). 2 layers, every hit masked.
  (A) CANONICAL   — exact patterns of .claude/hooks/post_write_secret_scan.ps1 (authoritative pack gate).
  (B) SUPPLEMENTARY — stricter (broad sk-/EAA, 9-19 digit runs w/ hex-context, psid literals, kw=value +pepper).
  Authoritative discriminators = canonical(A) + risk-excluded real-token count.
"""
import re, os

ROOT = r"D:\M6\Module6-workspace\04-artifacts"
TARGETS = [
    os.path.join(ROOT, "impl", "M6.2Q"),
    os.path.join(ROOT, "test-reports", "M6.2Q"),
    os.path.join(ROOT, "boundary-reports", "M6.2Q_boundary.md"),
    os.path.join(ROOT, "security-reports", "M6.2Q_security.md"),
]
EVID = os.path.join(ROOT, "evidence", "prompts")
for pid in ["M6-P2500","M6-P2501","M6-P2502","M6-P2503","M6-P2504","M6-P2505","M6-P2506"]:
    p = os.path.join(EVID, pid + ".json")
    if os.path.exists(p): TARGETS.append(p)

SKIP = {"__pycache__",".pytest_cache",".git","node_modules",".venv","venv","_source_snapshot"}
BIN = {".png",".jpg",".jpeg",".gif",".pdf",".zip",".docx",".xlsx",".pptx",".exe",".dll",".ico",".woff",".woff2",".ttf",".pyc"}

TOK = {"meta":r"EAA[A-Za-z0-9]{20,}","openai":r"sk-[A-Za-z0-9_\-]{20,}","gh":r"gh[pousr]_[A-Za-z0-9]{20,}",
       "slack":r"xox[baprs]-[A-Za-z0-9\-]{10,}","aws":r"AKIA[0-9A-Z]{16}","goog":r"AIza[0-9A-Za-z_\-]{30,}",
       "jwt":r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}"}
SEC = re.compile(r"(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key|verify[_-]?token|private[_-]?key|pepper)\b\s*[:=]\s*['\"]([^'\"\r\n]{12,})['\"]")
ALLOW = re.compile(r"^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)")
ID = re.compile(r"(?i)\b(user[_-]?id|customer[_-]?id|guest[_-]?id|psid|buyer[_-]?id|member[_-]?id)\b['\"]?\s*[:=]\s*['\"]?(\d{6,})")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PH1 = re.compile(r"(?<![A-Za-z0-9])(?:\+?84|0)\d{8,10}(?![A-Za-z0-9])")
PH2 = re.compile(r"(?<![A-Za-z0-9])(?:\+?84[ .\-]?|0)\d{2,3}[ .\-]\d{3,4}[ .\-]\d{3,4}(?![A-Za-z0-9])(?![ .\-]\d)")
SUP = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]{6,}|EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,})")
DIGIT = re.compile(r"(?<![0-9a-fA-F])[0-9]{9,19}(?![0-9a-fA-F])")
PSIDL = re.compile(r"(?i)\bpsid\s*[=:]\s*[\"'][^\"']{6,}[\"']")
ASSIGN = re.compile(r"(?i)(password|passwd|client_secret|api_key|apikey|access_token|verify_token|private_key|secret_key|token|pepper)\s*[=:]\s*[\"']?([A-Za-z0-9._\-/+]{8,})")
HI = re.compile(r"(EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,}|bearer\s+[A-Za-z0-9._-]{10,})")
HEX = re.compile(r"[0-9a-fA-F]{16,}")

def mask(s):
    s = "".join(ch for ch in s if ch.isprintable())
    return "***" if len(s) <= 6 else f"{s[:3]}***{s[-2:]}"
def preword(line, start):
    j = start
    while j > 0 and (line[j-1].isalnum() or line[j-1] in "-_"): j -= 1
    return line[j:start+3]
def iter_files():
    for t in TARGETS:
        if os.path.isfile(t): yield t
        elif os.path.isdir(t):
            for dp, dns, fns in os.walk(t):
                dns[:] = [d for d in dns if d not in SKIP]
                for fn in fns:
                    if os.path.splitext(fn)[1].lower() not in BIN: yield os.path.join(dp, fn)

canon = {"token":0,"sec":[],"id":[],"email":0,"phone":0}
sup = {"SUP":0,"DIGIT":[],"PSIDL":[]}
real_assign, real_token = [], []
files = 0
for fp in iter_files():
    try: text = open(fp, encoding="utf-8", errors="replace").read()
    except Exception as e: print("  !!", fp, e); continue
    files += 1
    rel = os.path.relpath(fp, ROOT)
    for n, rx in TOK.items():
        for m in re.finditer(rx, text): canon["token"] += 1; print("  TOKEN", n, rel, mask(m.group(0)))
    for m in SEC.finditer(text):
        if not ALLOW.match(m.group(2)): canon["sec"].append((rel, m.group(1), mask(m.group(2))))
    for m in ID.finditer(text): canon["id"].append((rel, m.group(1), mask(m.group(2))))
    canon["email"] += len(EMAIL.findall(text))
    canon["phone"] += len(PH1.findall(text)) + len(PH2.findall(text))
    for i, line in enumerate(text.splitlines(), 1):
        sup["SUP"] += len(SUP.findall(line))
        for m in DIGIT.finditer(line):
            note = "HEXCTX" if any(h.start() <= m.start() and h.end() >= m.end() for h in HEX.finditer(line)) else ""
            sup["DIGIT"].append((rel, i, mask(m.group(0)), note))
        for m in PSIDL.finditer(line): sup["PSIDL"].append((rel, i, mask(m.group(0))))
        for m in ASSIGN.finditer(line):
            v = m.group(2)
            if v.lower() in ("value","none","null","xxx","masked","secret_ref","abc","the","that","only","required","string","false","true"): continue
            real_assign.append((rel, i, m.group(1), mask(v)))
        for m in HI.finditer(line):
            tok = m.group(0)
            if tok.lower().startswith("sk-") and preword(line, m.start()).lower().startswith("ri"): continue
            real_token.append((rel, i, mask(tok), preword(line, m.start())))

print(f"=== FILES SCANNED: {files} ===")
print("(A) CANONICAL: token", canon["token"], "| secret-assign", len(canon["sec"]), "| raw user-id", len(canon["id"]), "| emails", canon["email"], "| phones", canon["phone"])
for r in canon["sec"][:20]: print("   sec:", r)
for r in canon["id"][:20]: print("   id:", r)
nonhex = [d for d in sup["DIGIT"] if d[3] != "HEXCTX"]
print("(B) SUPPLEMENTARY: broad sk-/EAA", sup["SUP"], "| DIGIT_RUN non-hex", len(nonhex), "| psid-literal", len(sup["PSIDL"]))
for r in nonhex[:25]: print("     digit:", r)
for r in sup["PSIDL"][:20]: print("     psid:", r)
print("AUTHORITATIVE: real kw=VALUE assignments", len(real_assign), "| real high-entropy tokens (risk-* excl)", len(real_token))
for r in real_assign[:40]: print("   ", r)
for r in real_token[:40]: print("   ", r)
