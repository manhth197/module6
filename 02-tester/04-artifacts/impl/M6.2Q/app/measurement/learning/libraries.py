"""M6.2H — the six ADS Strategy Libraries (doc §17, extract 338–345), seeded ONLY from canonical sources.

Guarded learning (RULE-011 / LEX-006): the machine NEVER fabricates origin strategy. Every `LibraryEntry` REQUIRES
a canonical `seed_source` valid for its library kind (per the doc §17 table); a missing / non-canonical source is
rejected. Content fill HALTS at framework while `LEARNING_CONTENT_FILL_ENABLED=False` (M6-OD-007 OPEN): an entry
carries a seed-source reference but NO machine-generated `content`. The layer reads canonical sources only — it
never writes pricing / program / policy (RULE-013/018).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app import config


class StrategyLibraryKind(str, Enum):
    """The six libraries (doc §17, verbatim order)."""

    PERSONA = "Persona Library"
    BEHAVIOR = "Behavior Library"
    KEYWORD = "Keyword Library"
    NEGATIVE_KEYWORD = "Negative Keyword Library"
    CREATIVE_HOOK = "Creative Hook Library"
    LANDING_CTA = "Landing / CTA Library"


# Purpose per library (doc §17 verbatim, extract 340–345).
LIBRARY_PURPOSE: Dict[StrategyLibraryKind, str] = {
    StrategyLibraryKind.PERSONA: "Nhóm khách mục tiêu",
    StrategyLibraryKind.BEHAVIOR: "Hành vi số và hành vi mua",
    StrategyLibraryKind.KEYWORD: "Từ khóa acquisition/intent",
    StrategyLibraryKind.NEGATIVE_KEYWORD: "Chặn tệp/ý định không phù hợp",
    StrategyLibraryKind.CREATIVE_HOOK: "Hook không sale sốc, đúng brand, đúng claim",
    StrategyLibraryKind.LANDING_CTA: "Mapping landing và CTA theo intent",
}

# The CANONICAL seed sources allowed per library (doc §17 table, verbatim tokens). A seed source NOT in the set
# for its library kind is NOT canonical -> rejected (RULE-011 seed-only-from-canon; LEX-006 no fabricated origin).
CANONICAL_SEED_SOURCES: Dict[StrategyLibraryKind, Tuple[str, ...]] = {
    StrategyLibraryKind.PERSONA: ("content_block_20_sku", "customer_context", "crm_lifecycle"),
    StrategyLibraryKind.BEHAVIOR: ("web_messenger_live_crm_events_dq_passed",),
    StrategyLibraryKind.KEYWORD: ("content_block", "product_public_view", "search_ads_history"),
    StrategyLibraryKind.NEGATIVE_KEYWORD: ("spam_troll_low_intent_fake_order_signals",),
    StrategyLibraryKind.CREATIVE_HOOK: ("product_effectiveness", "meta_safe_wording", "golden_hour_tri_an"),
    StrategyLibraryKind.LANDING_CTA: ("hero_sku", "golden_hour", "diamond", "crm_reorder"),
}


class LibrarySeedViolation(Exception):
    """Raised when a library entry is not seeded from a canonical source, or content is fabricated while content
    fill is BLOCKED (M6-OD-007) — the machine never fabricates origin strategy (RULE-011, LEX-006)."""


@dataclass(frozen=True)
class LibraryEntry:
    """One strategy-library entry. `seed_source` is REQUIRED and must be canonical for `kind`. `content` is the
    machine-generated origin strategy — it stays None while content fill is BLOCKED (framework-only, M6-OD-007)."""

    entry_id: str
    kind: StrategyLibraryKind
    seed_source: str
    purpose: str
    content: Optional[str] = None       # None while LEARNING_CONTENT_FILL_ENABLED is False (framework-only)


def is_canonical_seed(kind: StrategyLibraryKind, seed_source: Optional[str]) -> bool:
    return bool(seed_source) and seed_source in CANONICAL_SEED_SOURCES.get(kind, ())


class StrategyLibraryStore:
    """In-memory store of the six libraries. `seed()` enforces canonical-source + content-fill fail-closed."""

    def __init__(self) -> None:
        self._by_kind: Dict[StrategyLibraryKind, List[LibraryEntry]] = {k: [] for k in StrategyLibraryKind}

    def seed(
        self,
        kind: StrategyLibraryKind,
        seed_source: str,
        *,
        entry_id: str,
        content: Optional[str] = None,
    ) -> LibraryEntry:
        """Seed one entry into a library. Rejects a non-canonical / missing seed source, and rejects any content
        while content fill is BLOCKED (M6-OD-007 OPEN) — the machine never fabricates origin strategy."""
        if not is_canonical_seed(kind, seed_source):
            raise LibrarySeedViolation(
                f"{kind.value} must seed from a canonical source {CANONICAL_SEED_SOURCES[kind]}; "
                f"got {seed_source!r} (RULE-011, LEX-006 — no fabricated origin strategy)"
            )
        if content is not None and not config.LEARNING_CONTENT_FILL_ENABLED:
            raise LibrarySeedViolation(
                "content fill is BLOCKED (M6-OD-007 OPEN, LEARNING_CONTENT_FILL_ENABLED=False): the library stays "
                "framework-only; the machine never fabricates origin strategy (LEX-006)"
            )
        entry = LibraryEntry(
            entry_id=entry_id, kind=kind, seed_source=seed_source,
            purpose=LIBRARY_PURPOSE[kind], content=content,
        )
        self._by_kind[kind].append(entry)
        return entry

    def entries(self, kind: StrategyLibraryKind) -> Tuple[LibraryEntry, ...]:
        return tuple(self._by_kind[kind])

    def has_seed(self, kind: StrategyLibraryKind) -> bool:
        return bool(self._by_kind[kind])

    def seeded_kinds(self) -> Tuple[StrategyLibraryKind, ...]:
        return tuple(k for k in StrategyLibraryKind if self._by_kind[k])

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_kind.values())
