import sys
sys.path.insert(0, r"D:/M6/Module6-workspace/01-coder/04-artifacts/impl/M6.2K")
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, SmokeResult
from app.measurement.evidence.categories import CATEGORY_MANDATORY
from app.measurement.evidence.smoke_registry import SMOKE_REGISTRY, get_spec, SmokeStatus

A = EvidencePackAssembler()
full_refs = {c: {k: 'r' for k in ks} for c, ks in CATEGORY_MANDATORY.items()}
# Run all smokes EXCEPT waive a mandatory OWNER smoke (SMK-001) that was never executed
sm = {}
for s in SMOKE_REGISTRY:
    if s.smoke_id == 'M6-SMK-001':
        sm[s.smoke_id] = SmokeResult(s.smoke_id, waived=True)   # owner smoke, never run, just waived
    else:
        sm[s.smoke_id] = SmokeResult(s.smoke_id, 'PASS', 'c', 'e')

p = A.assemble(smoke_results=sm, evidence_refs=full_refs)
print('SMK-001 status in registry:', get_spec('M6-SMK-001').status.value)
print('SMK-001 recorded via waiver:', sm['M6-SMK-001'].recorded)
print('readiness with a WAIVED mandatory owner smoke:', p.readiness.value)
print('unrecorded smokes:', [s.smoke_id for s in p.unrecorded_smokes()])
