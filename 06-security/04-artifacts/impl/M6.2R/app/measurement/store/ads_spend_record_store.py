"""Set-once in-memory store for MATERIALIZED ads-spend records (M6.2Q, A5).

Holds ONLY the spend records the materializer wrote from an APPROVED import (M6-OD-016). Materialization is SET-ONCE
per import: an identical re-materialize is an idempotent no-op; an ALTERED re-materialize is refused loudly
(AdsSpendRecordStoreViolation) — never a silent overwrite. There is NO update/delete surface. The records are
CONSUMED-style facts (campaign-level spend, not PII) read by the by-session CPA/ROAS reader (session_roas).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from app.measurement.dashboard.data_mart import AdsSpendRecord


class AdsSpendRecordStoreViolation(Exception):
    """Raised on a forbidden op: a second/altered materialize of an import, or an update/delete."""


class AdsSpendRecordStore:
    def __init__(self) -> None:
        self._by_import: Dict[str, Tuple[AdsSpendRecord, ...]] = {}
        self._order: List[str] = []

    def materialize_import(self, import_id: str, records: Tuple[AdsSpendRecord, ...]) -> Tuple[AdsSpendRecord, ...]:
        records = tuple(records)
        existing = self._by_import.get(import_id)
        if existing is not None:
            if existing == records:
                return existing                       # idempotent replay — no overwrite
            raise AdsSpendRecordStoreViolation(
                f"ads_spend import {import_id} already materialized (set-once): a correction is a NEW import, "
                "never an in-place overwrite"
            )
        self._by_import[import_id] = records
        self._order.append(import_id)
        return records

    def is_materialized(self, import_id: str) -> bool:
        return import_id in self._by_import

    def records_for_import(self, import_id: str) -> Tuple[AdsSpendRecord, ...]:
        return self._by_import.get(import_id, ())

    def all(self) -> Tuple[AdsSpendRecord, ...]:
        out: List[AdsSpendRecord] = []
        for i in self._order:
            out.extend(self._by_import[i])
        return tuple(out)

    def __len__(self) -> int:
        return sum(len(self._by_import[i]) for i in self._order)

    # --- forbidden-op guards (set-once immutability) — fail loudly, never silently ------------------
    def update(self, *args, **kwargs):
        raise AdsSpendRecordStoreViolation("materialized ads-spend records are set-once (UPDATE forbidden)")

    def delete(self, *args, **kwargs):
        raise AdsSpendRecordStoreViolation("materialized ads-spend records forbid DELETE / history rewrite")
