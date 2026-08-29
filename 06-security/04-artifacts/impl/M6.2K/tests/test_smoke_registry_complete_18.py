"""M6.2K leg L1: the smoke registry lists all 18 P0 smokes (SMK-001..018) with scenario/expected + bound test
files; SMK-016/017/018 are `proposed` (executed OR owner-waived). Every registered smoke binds to a real test
file under tests/smoke/.
"""
from __future__ import annotations

import glob
import os

from app.measurement.evidence.smoke_registry import (
    SMOKE_IDS,
    SMOKE_REGISTRY,
    SmokeStatus,
    proposed_ids,
)

_SMOKE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "smoke")


def test_registry_has_all_18_smoke_ids():
    assert len(SMOKE_REGISTRY) == 18
    assert SMOKE_IDS == tuple(f"M6-SMK-{n:03d}" for n in range(1, 19))


def test_owner_and_proposed_split():
    owner = [s for s in SMOKE_REGISTRY if s.status is SmokeStatus.OWNER]
    proposed = [s for s in SMOKE_REGISTRY if s.status is SmokeStatus.PROPOSED]
    assert len(owner) == 15                                   # ADS-P0-001..015
    assert proposed_ids() == ("M6-SMK-016", "M6-SMK-017", "M6-SMK-018")
    assert len(proposed) == 3


def test_every_smoke_scenario_and_expected_present():
    for s in SMOKE_REGISTRY:
        assert s.scenario and s.expected, f"{s.smoke_id} missing scenario/expected"


def test_every_smoke_binds_to_a_real_test_file():
    # the smoke suite lives next to this test dir; each smoke's glob must match >= 1 file
    smoke_dir = os.path.join(os.path.dirname(__file__), "smoke")
    for s in SMOKE_REGISTRY:
        matches = glob.glob(os.path.join(smoke_dir, s.test_glob))
        assert matches, f"{s.smoke_id} glob {s.test_glob} matched no file in {smoke_dir}"
