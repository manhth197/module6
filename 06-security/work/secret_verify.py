"""Categorize SECRET hits; flag any real keyword=VALUE assignment (masked)."""
import re, os

ROOT = r"D:\M6\Module6-workspace\04-artifacts"
TARGETS = [os.path.join(ROOT, "impl", "M6.2A"),
           os.path.join(ROOT, "test-reports", "M6.2A"),
           os.path.join(ROOT, "boundary-reports", "M6.2A_boundary.md"),
           os.path.join(ROOT, "security-reports", "M6.2A_security.md")]
EVID = os.path.join(ROOT, "evidence", "prompts")
for pid in ["M6-P1000","M6-P1001","M6-P1002","M6-P1003","M6-P1004","M6-P1005","M6-P1006"]:
    p = os.path.join(EVID, pid + ".json")
    if os.path.exists(p): TARGETS.append(p)
SKIP = {"__pycache__",".pytest_cache",".git"}

RISK = re.compile(r"risk-accept", re.I)
# keyword immediately followed by an assignment and a value with entropy
ASSIGN = re.compile(r"(?i)(password|passwd|client_secret|api_key|apikey|access_token|verify_token|private_key|secret_key|token)\s*[=:]\s*[\"']?([A-Za-z0-9._\-/+]{8,})")
HIGH_ENTROPY_TOKEN = re.compile(r"(EAA[A-Za-z0-9]{6,}|sk-[A-Za-z0-9]{6,}|AKIA[0-9A-Z]{10,}|ghp_[A-Za-z0-9]{6,}|xox[baprs]-[A-Za-z0-9-]{6,}|bearer\s+[A-Za-z0-9._-]{10,})")

def mask(s):
    s="".join(c for c in s if c.isprintable())
    return "***" if len(s)<=5 else f"{s[:3]}***{s[-2:]}"

def files():
    for t in TARGETS:
        if os.path.isfile(t): yield t
        elif os.path.isdir(t):
            for dp,dns,fns in os.walk(t):
                dns[:]=[d for d in dns if d not in SKIP]
                for fn in fns:
                    if not fn.endswith(".pyc"): yield os.path.join(dp,fn)

real_assign=[]; real_token=[]
for fp in files():
    try: txt=open(fp,encoding="utf-8",errors="replace").read().splitlines()
    except: continue
    rel=os.path.relpath(fp,ROOT)
    for i,l in enumerate(txt,1):
        for m in ASSIGN.finditer(l):
            kw,val=m.group(1),m.group(2)
            # exclude doc-ish placeholders
            if val.lower() in ("value","none","null","xxx","masked","secret_ref","abc","the","that","only"): continue
            real_assign.append((rel,i,kw,mask(val)))
        for m in HIGH_ENTROPY_TOKEN.finditer(l):
            tok=m.group(0)
            if RISK.search(l) and tok.lower().startswith("sk-"):  # 'risk-accept...'
                continue
            real_token.append((rel,i,mask(tok),tok[:3]))

print("=== keyword=VALUE assignments (excluding placeholders) ===")
print("  count:", len(real_assign))
for r in real_assign[:40]: print("  ", r)
print("\n=== high-entropy platform tokens (excluding 'risk-accept*' sk- false positives) ===")
print("  count:", len(real_token))
for r in real_token[:40]: print("  ", r)
