"""M6.2H leg 1 / M6-OD-007: content fill HALTS at framework. While LEARNING_CONTENT_FILL_ENABLED is False, a
library entry carries a canonical seed-source reference but NO machine-generated content — the framework proceeds,
content is BLOCKED (the machine never fabricates origin strategy, LEX-006).
"""
from __future__ import annotations

import pytest

from app import config
from app.measurement.learning.libraries import LibrarySeedViolation, StrategyLibraryKind


def test_content_fill_is_blocked_by_config():
    assert config.LEARNING_CONTENT_FILL_ENABLED is False   # M6-OD-007 OPEN -> framework-only


def test_framework_entry_has_no_content(library_store):
    entry = library_store.seed(StrategyLibraryKind.CREATIVE_HOOK, "meta_safe_wording", entry_id="h1")
    assert entry.content is None                            # framework proceeds, content halted
    assert entry.seed_source == "meta_safe_wording"
    assert entry.purpose == "Hook không sale sốc, đúng brand, đúng claim"   # locked purpose (doc §17)


def test_attempting_to_fill_content_is_rejected(library_store):
    # supplying machine-generated content while content fill is BLOCKED (M6-OD-007) is refused (LEX-006)
    with pytest.raises(LibrarySeedViolation):
        library_store.seed(StrategyLibraryKind.CREATIVE_HOOK, "meta_safe_wording",
                           entry_id="h2", content="Buy now! Best deal ever!")
