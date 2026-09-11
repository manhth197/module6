"""M6.2H leg 1 / M6-RULE-011 / M6-LEX-006: the six libraries seed ONLY from canonical sources; a missing or
non-canonical seed source is REJECTED. The machine never fabricates origin strategy ("không để machine tự bịa
chiến lược gốc", doc §17). LEX-006 is the doc's FORBIDDEN cell.
"""
from __future__ import annotations

import pytest

from app.measurement.learning.libraries import (
    CANONICAL_SEED_SOURCES,
    LibrarySeedViolation,
    StrategyLibraryKind,
    StrategyLibraryStore,
)


def test_all_six_libraries_exist():
    assert len(StrategyLibraryKind) == 6
    assert {k for k in StrategyLibraryKind} == {
        StrategyLibraryKind.PERSONA, StrategyLibraryKind.BEHAVIOR, StrategyLibraryKind.KEYWORD,
        StrategyLibraryKind.NEGATIVE_KEYWORD, StrategyLibraryKind.CREATIVE_HOOK, StrategyLibraryKind.LANDING_CTA,
    }


def test_canonical_seed_is_accepted(library_store):
    entry = library_store.seed(StrategyLibraryKind.PERSONA, "content_block_20_sku", entry_id="p1")
    assert entry.seed_source == "content_block_20_sku"
    assert library_store.has_seed(StrategyLibraryKind.PERSONA)


@pytest.mark.parametrize("kind", list(StrategyLibraryKind))
def test_missing_seed_source_is_rejected(library_store, kind):
    with pytest.raises(LibrarySeedViolation):
        library_store.seed(kind, "", entry_id="bad")


@pytest.mark.parametrize("kind", list(StrategyLibraryKind))
def test_non_canonical_seed_source_is_rejected(library_store, kind):
    # a machine-fabricated / non-canonical origin source is refused (LEX-006)
    with pytest.raises(LibrarySeedViolation):
        library_store.seed(kind, "machine_made_up_origin", entry_id="fabricated")


def test_each_library_only_accepts_its_own_canonical_sources(library_store):
    # a source canonical for Persona is NOT canonical for Keyword -> rejected (seed-only-from-canon per kind)
    persona_src = CANONICAL_SEED_SOURCES[StrategyLibraryKind.PERSONA][0]
    assert persona_src not in CANONICAL_SEED_SOURCES[StrategyLibraryKind.KEYWORD]
    with pytest.raises(LibrarySeedViolation):
        library_store.seed(StrategyLibraryKind.KEYWORD, persona_src, entry_id="x")
