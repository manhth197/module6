"""M6-P1006 SECURITY_PII independent scan. Masks every hit; no raw PII is ever printed."""
import re, os

ROOT = r"D:\M6\Module6-workspace\04-artifacts"
TARGETS = [
    os.path.join(ROOT, "impl", "M6.2A"),
    os.path.join(ROOT, "test-reports", "M6.2A"),
    os.path.join(ROOT, "boundary-reports", "M6.2A_boundary.md"),
    os.path.join(ROOT, "security-reports", "M6.2A_security.md"),
]
EVID = os.path.join(ROOT, "evidence", "prompts")
for pid in ["M6-P1000","M6-P1001","M6-P1002","M6-P1003","M6-P1004","M6-P1005","M6-P1006"]:
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
HEXCTX = re.compile(r"[0-9a-fA-F]{16,}")

def mask(s):
    s = "".join(ch for ch in s if ch.isprintable())
    if len(s) <= 5:
        return "***"
    return f"{s[:3]}***{s[-2:]}"

def iter_files():
    for t in TARGETS:
        if os.path.isfile(t):
            yield t
        elif os.path.isdir(t):
            for dp, dns, fns in os.walk(t):
                dns[:] = [d for d in dns if d not in SKIP_DIRS]
                for fn in fns:
                    if fn.endswith(".pyc"):
                        continue
                    yield os.path.join(dp, fn)

hits = {k: [] for k in PATTERNS}
files_scanned = 0
for fp in iter_files():
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  !! cannot read {fp}: {e}")
        continue
    files_scanned += 1
    rel = os.path.relpath(fp, ROOT)
    for i, line in enumerate(lines, 1):
        for name, pat in PATTERNS.items():
            for m in pat.finditer(line):
                val = m.group(0)
                in_hex = False
                if name == "DIGIT_RUN_9_19":
                    for hm in HEXCTX.finditer(line):
                        if hm.start() <= m.start() and hm.end() >= m.end():
                            in_hex = True
                            break
                hits[name].append((rel, i, mask(val), len(val), "HEXCTX" if in_hex else ""))

print(f"=== FILES SCANNED: {files_scanned} ===")
for name in PATTERNS:
    hs = hits[name]
    print(f"\n### {name}: {len(hs)} raw regex hits")
    for rel, ln, mv, length, note in hs[:30]:
        print(f"   {rel}:{ln}  masked={mv} len={length} {note}")
    if len(hs) > 30:
        print(f"   ... +{len(hs)-30} more")
