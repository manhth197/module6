"""M6.2K leg L1 (meta): a coder-level sanity check that the carried full P0 smoke suite is present + collectable —
every registered smoke id maps to at least one test file under tests/smoke/. The OFFICIAL P0 re-run with recorded
correlation_id + evidence_id is the TESTER's (M6-P2003/2004); no self-run / self-certify here (RULE-015).
"""
from __future__ import annotations

import glob
import os

from app.measurement.evidence.smoke_registry import SMOKE_REGISTRY

_SMOKE_DIR = os.path.join(os.path.dirname(__file__), "smoke")


def test_smoke_directory_present():
    assert os.path.isdir(_SMOKE_DIR), "the carried smoke suite directory is missing"


def test_every_registered_smoke_has_a_file():
    missing = [s.smoke_id for s in SMOKE_REGISTRY if not glob.glob(os.path.join(_SMOKE_DIR, s.test_glob))]
    assert not missing, f"registered smokes with no test file: {missing}"


def test_suite_covers_all_18_ids():
    files = glob.glob(os.path.join(_SMOKE_DIR, "test_smk_*.py"))
    covered = {os.path.basename(f)[len("test_smk_"):len("test_smk_") + 3] for f in files}
    expected = {f"{n:03d}" for n in range(1, 19)}
    assert expected <= covered, f"smoke files missing for ids: {sorted(expected - covered)}"
