"""M6.2K leg L1 / RULE-H01 / RULE-014: the pack records the immutable staged posture (BLOCKED/OFF/OFF + all flags)
and exposes no method to change it; every export is PII-safe (correlation_id / evidence_id masked; no raw value).
"""
from __future__ import annotations

from app import config


def test_pack_records_immutable_posture(evidence_assembler):
    pack = evidence_assembler.assemble()
    p = pack.posture
    assert p["global_gateway_state"] == "BLOCKED"
    assert p["production_flag"] == "OFF"
    assert p["external_send"] == "OFF"
    assert p["scale_execution_enabled"] == "False"
    assert p["learning_autopublish_enabled"] == "False"
    # the recorded posture matches the immutable config (nothing enabling)
    assert p["global_gateway_state"] == config.GLOBAL_GATEWAY_STATE
    assert p["production_flag"] == config.PRODUCTION_FLAG


def test_pack_exposes_no_posture_mutator(evidence_assembler):
    pack = evidence_assembler.assemble()
    for verb in ("set_posture", "set_production_flag", "enable", "flip", "unblock", "write"):
        assert not hasattr(pack, verb), f"EvidencePack exposes posture mutator {verb!r}"


def test_posture_snapshot_is_read_only(evidence_assembler):
    """Defense-in-depth (adversarial review): the recorded posture snapshot cannot be tampered in-memory
    (e.g. production_flag flipped to 'ON') — it is a read-only mapping."""
    import pytest
    pack = evidence_assembler.assemble()
    with pytest.raises(TypeError):
        pack.posture["production_flag"] = "ON"     # read-only (MappingProxyType) -> raises
    assert pack.posture["production_flag"] == "OFF"


def test_smoke_export_masks_correlation_and_evidence_ids(evidence_assembler, make_smoke_result):
    corr, ev = "corr_verylong_secret_value", "ev_verylong_secret_value"
    results = {"M6-SMK-001": make_smoke_result("M6-SMK-001", correlation_id=corr, evidence_id=ev)}
    pack = evidence_assembler.assemble(results)
    smk = next(s for s in pack.to_public()["smokes"] if s["smoke_id"] == "M6-SMK-001")
    assert smk["correlation_id"] != corr and smk["correlation_id"] is not None    # masked, not raw
    assert smk["evidence_id"] != ev and smk["evidence_id"] is not None
    assert corr not in str(pack.to_public()) and ev not in str(pack.to_public())


def test_gap_blockers_carry_no_pii(evidence_assembler):
    pack = evidence_assembler.assemble()
    blob = str(pack.to_public()["gap_blockers"])
    # governance refs only (ids like M6-P1000 / M6-OD-011); no email/phone markers
    assert "@" not in blob
