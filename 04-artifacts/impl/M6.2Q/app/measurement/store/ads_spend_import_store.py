"""Inert in-memory store for ads_spend_import proposals + their maker-checker lifecycle (M6.2Q, M6-OD-016).

A lifecycle transition (PROPOSED -> APPROVED/REJECTED) REPLACES the current record and appends to an append-only
history — it is data, never a real spend or send. This store has NO method that fetches spend from a network,
calls the Marketing API, or executes anything (M6-OD-016 phase-1 CSV only). Mirrors ScaleRequestStore. The physical
DB binding is the M6-OD-011 integration step (migration 0014, live_migrations=false).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.measurement.models.ads_spend_import import AdsSpendImport


class AdsSpendImportStoreViolation(Exception):
    """Raised on a forbidden op (duplicate create / unknown update)."""


class AdsSpendImportStore:
    def __init__(self) -> None:
        self._by_id: Dict[str, AdsSpendImport] = {}
        self._order: List[str] = []
        self._history: List[AdsSpendImport] = []   # append-only lifecycle trail

    def create(self, import_: AdsSpendImport) -> AdsSpendImport:
        if import_.import_id in self._by_id:
            raise AdsSpendImportStoreViolation(f"ads_spend_import {import_.import_id} already exists")
        self._by_id[import_.import_id] = import_
        self._order.append(import_.import_id)
        self._history.append(import_)
        return import_

    def update_state(self, import_: AdsSpendImport) -> AdsSpendImport:
        """Persist a lifecycle transition (a NEW frozen record, same import_id). Append-only history."""
        if import_.import_id not in self._by_id:
            raise AdsSpendImportStoreViolation(f"cannot update unknown ads_spend_import {import_.import_id}")
        self._by_id[import_.import_id] = import_
        self._history.append(import_)
        return import_

    def get(self, import_id: str) -> Optional[AdsSpendImport]:
        return self._by_id.get(import_id)

    def all(self) -> Tuple[AdsSpendImport, ...]:
        return tuple(self._by_id[i] for i in self._order)

    @property
    def history(self) -> Tuple[AdsSpendImport, ...]:
        return tuple(self._history)

    def __len__(self) -> int:
        return len(self._order)
