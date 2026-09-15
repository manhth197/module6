"""M6.2H leg 1 / M6-LEX-005 / M6-RULE-013/018: the SKU -> Persona -> ... -> Verified Revenue mapping chain
resolves and every mapping is ANCHORED to a sellable SKU. The layer reads canonical refs only — it never writes
pricing / program / policy (no Core-policy override) and computes no commission (RULE-019).
"""
from __future__ import annotations

import pytest

from app.measurement.learning.mapping import StrategyMapping, StrategyMappingViolation


def test_mapping_requires_a_sellable_sku():
    with pytest.raises(StrategyMappingViolation):
        StrategyMapping(sku_ref="")                                  # not anchored to a sellable SKU (LEX-005)


def test_full_chain_resolves():
    m = StrategyMapping(
        sku_ref="SKU_HERO_1", persona="p1", behavior="b1", keyword="k1", creative_hook="h1",
        landing="l1", cta="c1", event_ref="evt_1", verified_revenue_ref="rev_1",
    )
    pub = m.to_public()
    assert pub["sku_ref"] == "SKU_HERO_1"
    assert (pub["persona"], pub["keyword"], pub["cta"]) == ("p1", "k1", "c1")
    assert pub["verified_revenue_ref"] == "rev_1"                    # a ref, never a revenue value


def test_run_records_active_mapping(learning_engine):
    m = StrategyMapping(sku_ref="SKU_HERO_1", persona="p1")
    learning_engine.run(m)
    assert learning_engine.active_mappings == (m,)


def test_mapping_never_writes_core_policy():
    m = StrategyMapping(sku_ref="SKU_1")
    for name in ("set_price", "write_price", "set_policy", "update_core", "publish", "commission", "scale"):
        assert not hasattr(m, name)                                 # RULE-013/018 (no Core override), RULE-019
