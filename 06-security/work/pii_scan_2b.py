"""M6-P1106 SECURITY_PII independent scan (slice M6.2B). Masks every hit; no raw PII printed."""
import re, os

ROOT = r"D:\M6\Module6-workspace\04-artifacts"
TARGETS = [
    os.path.join(ROOT, "impl", "M6.2B"),
    os.path.join(ROOT, "test-reports", "M6.2B"),
    os.path.join(ROOT, "boundary-reports", "M6.2B_boundary.md"),
    os.path.join(ROOT, "security-reports", "M6.2B_security.md"),
]
EVID = os.path.join(ROOT, "evidence", "prompts")
for pid in ["M6-P1100","M6-P1101","M6-P1102","M6-P1103","M6-P1104","M6-P1105","M6-P1106"]:
    p = os.path.join(EVID, pid + ".json")
    if os.path.exists(p):
        TARGETS.append(p)

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv", "venv"}

PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "VN_PHONE": re.compile(r"(?<![0-9])(?:\+?84|0)(?:3|5|7|8|9)[0-9]{8}(?![0-9])"),
    "DIGIT_RUN_9_19": re.compile(r"(?<![0-9a-fA-F])[0-9]{9,19}(?![0-9a-fA-F])"),
    "SECRET": re.compile(r"(?i)(password|passwd|client_secret|api_key|apikey|access_token|verify_token|private_key|secret_key|bearer\s+[A-Za-z0-9._-]{6,}|EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,})"),
}
ASSIGN = re.compile(r"(?i)(password|passwd|client_secret|api_key|apikey|access_token|verify_token|private_key|secret_key|token)\s*[=:]\s*[\"']?([A-Za-z0-9._\-/+]{8,})")
HIGH_ENTROPY = re.compile(r"(EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,}|bearer\s+[A-Za-z0-9._-]{10,})")
RISK = re.compile(r"risk-?accept", re.I)
HEXCTX = re.compile(r"[0-9a-fA-F]{16,}")

def mask(s):
    s = "".join(ch for ch in s if ch.isprintable())
    return "***" if len(s) <= 5 else f"{s[:3]}***{s[-2:]}"

def iter_files():
    for t in TARGETS:
        if os.path.isfile(t):
            yield t
        elif os.path.isdir(t):
            for dp, dns, fns in os.walk(t):
                dns[:] = [d for d in dns if d not in SKIP_DIRS]
                for fn in fns:
                    if not fn.endswith(".pyc"):
                        yield os.path.join(dp, fn)

hits = {k: [] for k in PATTERNS}
real_assign, real_token = [], []
files_scanned = 0
for fp in iter_files():
    try:
        lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
    except Exception as e:
        print("  !! cannot read", fp, e); continue
    files_scanned += 1
    rel = os.path.relpath(fp, ROOT)
    for i, line in enumerate(lines, 1):
        for name, pat in PATTERNS.items():
            for m in pat.finditer(line):
                val = m.group(0)
                note = ""
                if name == "DIGIT_RUN_9_19":
                    for hm in HEXCTX.finditer(line):
                        if hm.start() <= m.start() and hm.end() >= m.end():
                            note = "HEXCTX"; break
                hits[name].append((rel, i, mask(val), len(val), note))
        for m in ASSIGN.finditer(line):
            kw, v = m.group(1), m.group(2)
            if v.lower() in ("value","none","null","xxx","masked","secret_ref","abc","the","that","only","required"): continue
            real_assign.append((rel, i, kw, mask(v)))
        for m in HIGH_ENTROPY.finditer(line):
            tok = m.group(0)
            if RISK.search(line) and tok.lower().startswith("sk-"): continue
            real_token.append((rel, i, mask(tok)))

print(f"=== FILES SCANNED: {files_scanned} ===")
for name in PATTERNS:
    hs = hits[name]
    print(f"\n### {name}: {len(hs)} raw regex hits")
    for rel, ln, mv, length, note in hs[:20]:
        print(f"   {rel}:{ln}  masked={mv} len={length} {note}")
    if len(hs) > 20:
        print(f"   ... +{len(hs)-20} more")
print("\n### REAL keyword=VALUE assignments (placeholders excluded):", len(real_assign))
for r in real_assign[:40]: print("   ", r)
print("### REAL high-entropy tokens (risk-accept excluded):", len(real_token))
for r in real_token[:40]: print("   ", r)
