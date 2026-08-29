import sys
sys.path.insert(0, r"D:/M6/Module6-workspace/01-coder/04-artifacts/impl/M6.2K")
from app.measurement.evidence.pack_assembler import EvidencePackAssembler
from app.measurement.evidence.models import Readiness, SmokeResult
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY
from app.measurement.evidence.smoke_registry import SMOKE_REGISTRY

A = EvidencePackAssembler()
def full_refs():
    return {c: {k: 'r' for k in ks} for c, ks in CATEGORY_MANDATORY.items()}
def full_smokes():
    return {s.smoke_id: SmokeResult(s.smoke_id, 'PASS', 'c', 'e') for s in SMOKE_REGISTRY}

refs = full_refs()
first_cat = EvidenceCategory.DASHBOARD
key0 = CATEGORY_MANDATORY[first_cat][0]
refs[first_cat].pop(key0)
p = A.assemble(smoke_results=full_smokes(), evidence_refs=refs)
cs = p.category(first_cat)
print('MISSING-KEY: complete=', cs.complete, '| missing=', cs.missing, '| readiness=', p.readiness.value)

for falsy in ['', None, 0, False, {}, []]:
    refs = full_refs(); refs[first_cat][key0] = falsy
    p = A.assemble(smoke_results=full_smokes(), evidence_refs=refs)
    print('FALSY-REF', repr(falsy), '-> complete=', p.category(first_cat).complete, 'readiness=', p.readiness.value)

sm = full_smokes(); sm.pop('M6-SMK-001')
p = A.assemble(smoke_results=sm, evidence_refs=full_refs())
print('OWNER-UNRUN: readiness=', p.readiness.value, '| unrecorded=', [s.smoke_id for s in p.unrecorded_smokes()])

sm = full_smokes(); sm.pop('M6-SMK-016')
p = A.assemble(smoke_results=sm, evidence_refs=full_refs())
print('PROPOSED-UNRUN-UNWAIVED: readiness=', p.readiness.value)

sm = full_smokes(); sm['M6-SMK-016'] = SmokeResult('M6-SMK-016', waived=True)
p = A.assemble(smoke_results=sm, evidence_refs=full_refs())
print('PROPOSED-WAIVED: recorded=', sm['M6-SMK-016'].recorded, '| readiness=', p.readiness.value)

print('HALF status-only:', SmokeResult('X', status='PASS').recorded)
print('HALF status+corr no evid:', SmokeResult('X', status='PASS', correlation_id='c').recorded)
print('HALF status+evid no corr:', SmokeResult('X', status='PASS', evidence_id='e').recorded)
print('HALF corr+evid no status:', SmokeResult('X', correlation_id='c', evidence_id='e').recorded)
print('HALF empty-string fields:', SmokeResult('X', status='', correlation_id='', evidence_id='').recorded)

sm = full_smokes(); sm['M6-SMK-002'] = SmokeResult('M6-SMK-002', status='PASS', correlation_id='c')
p = A.assemble(smoke_results=sm, evidence_refs=full_refs())
print('HALF-IN-PACK: readiness=', p.readiness.value)
