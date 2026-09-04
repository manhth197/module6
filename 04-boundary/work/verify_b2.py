from app.measurement.evidence.pack_assembler import EvidencePackAssembler, _ref_valid, _ref_binding
from app.measurement.evidence.categories import EvidenceCategory, CATEGORY_MANDATORY

A = EvidencePackAssembler()

forged = {}
for cat in EvidenceCategory:
    forged[cat] = {k: 'ev::%s::%s' % (cat.value, k) for k in CATEGORY_MANDATORY[cat]}
pack = A.assemble(smoke_results=None, evidence_refs=forged)
print('V1 all categories complete:', all(c.complete for c in pack.categories))
print('V1 readiness:', pack.readiness.value)
print('V1 standing blockers still disclosed:', pack.has_standing_blockers())

er = {k: 'ev::Event Registry::%s' % k for k in CATEGORY_MANDATORY[EvidenceCategory.EVENT_REGISTRY]}
pack2 = A.assemble(evidence_refs={EvidenceCategory.EVENT_REGISTRY: er})
print('V2 EVENT_REGISTRY complete via forge:', pack2.category(EvidenceCategory.EVENT_REGISTRY).complete)

counts = {'ev::Consent::consent_pass': 2}
print('V3 copy-paste passes?', _ref_valid('ev::Consent::consent_pass', EvidenceCategory.CONSENT, 'consent_pass', counts, None))

print('V4 junk x:', _ref_valid('x', EvidenceCategory.CONSENT,'consent_pass',{'x':1},None))
print('V4 whitespace:', _ref_valid('   ', EvidenceCategory.CONSENT,'consent_pass',{'':1},None))

print('V5 wrong-cat:', _ref_valid('ev::Event Registry::consent_pass', EvidenceCategory.CONSENT,'consent_pass',{'ev::Event Registry::consent_pass':1},None))
print('V5 case-variant:', _ref_valid('ev::consent::consent_pass', EvidenceCategory.CONSENT,'consent_pass',{'ev::consent::consent_pass':1},None))
print('V5 extra-seg binding:', _ref_binding('ev::Consent::consent::pass'))
padded = {EvidenceCategory.CONSENT: {'consent_pass':'ev::Consent::consent_pass','consent_fail_closed':' ev::Consent::consent_pass '}}
p5 = A.assemble(evidence_refs=padded)
print('V5 padded-dup present:', p5.category(EvidenceCategory.CONSENT).present)

print('V6 non-str int:', _ref_valid(12345, EvidenceCategory.CONSENT,'consent_pass',{},None))
print('V6 non-str bytes:', _ref_valid(b'ev::Consent::consent_pass', EvidenceCategory.CONSENT,'consent_pass',{},None))

class Evil:
    def __contains__(self, x): return True
print('V7 hostile oracle passes forged:', _ref_valid('ev::Consent::consent_pass', EvidenceCategory.CONSENT,'consent_pass',{'ev::Consent::consent_pass':1},Evil()))

try:
    A.assemble(evidence_refs={EvidenceCategory.CONSENT: ['ev::Consent::consent_pass']})
    print('V8 no crash')
except Exception as e:
    print('V8 crash:', type(e).__name__, str(e))
