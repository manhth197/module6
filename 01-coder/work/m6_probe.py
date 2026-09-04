import sys
sys.path.insert(0, r"D:/M6/Module6-workspace/01-coder/04-artifacts/impl/M6.2L")
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.smoke_registry import SMOKE_IDS
from app.measurement.evidence.models import SmokeResult, Readiness

full = {cat: {k: f"ev::{cat.value}::{k}" for k in keys} for cat, keys in CATEGORY_MANDATORY.items()}
smokes = {sid: SmokeResult(smoke_id=sid, status="PASS", correlation_id="c"+sid[-3:], evidence_id="e"+sid[-3:]) for sid in SMOKE_IDS}
asm = EvidencePackAssembler()

all_refs = {v for cat in full for v in full[cat].values()}

target_cat = EvidenceCategory.EVENT_REGISTRY
target_key = "policy"
target_ref = full[target_cat][target_key]
allowlist = all_refs - {target_ref}
print("target_ref =", target_ref, "| in allowlist:", target_ref in allowlist)

pack = asm.assemble(smokes, full, known_refs=allowlist)
tc = pack.category(target_cat)
print("[allowlist] target complete:", tc.complete, "missing:", tc.missing)
others = [c.category.value for c in pack.categories if c.category is not target_cat and not c.complete]
print("[allowlist] other incomplete cats:", others)
print("[allowlist] readiness:", pack.readiness)

pack2 = asm.assemble(smokes, full)
inc2 = [c.category.value for c in pack2.categories if not c.complete]
print("[no-oracle] incomplete cats:", inc2, "readiness:", pack2.readiness)

pack3 = asm.assemble(smokes, full, known_refs=all_refs)
inc3 = [c.category.value for c in pack3.categories if not c.complete]
print("[full-allowlist] incomplete cats:", inc3, "readiness:", pack3.readiness)

print("=== leg-2 ===")
ws = SmokeResult(smoke_id="M6-SMK-001", status="  ", correlation_id="\t", evidence_id=" ")
print("whitespace recorded (current raw-truthiness):", ws.recorded)
none = SmokeResult(smoke_id="M6-SMK-001")
print("none recorded:", none.recorded)

# Does whitespace-recorded smoke currently mark pack ready? (simulate all recorded except SMK-001 whitespace)
sm2 = dict(smokes)
sm2["M6-SMK-001"] = ws
p = asm.assemble(sm2, full)
smk = next(s for s in p.smokes if s.smoke_id == "M6-SMK-001")
print("pack SMK-001 recorded:", smk.recorded, "| readiness:", p.readiness)
print("to_public status/corr/ev:", smk.to_public()["status"], repr(smk.to_public()["correlation_id"]))
