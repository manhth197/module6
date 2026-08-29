"""Inert in-memory store for ads_scale_request proposals + their lifecycle records (M6.2G, CTR-013/026).

A lifecycle transition (PROPOSED -> APPROVED/REJECTED) REPLACES the current record and appends to an append-only
history — it is data, never an executed action (RULE-010). This store has NO method that raises a budget, enables
a campaign, opens audience scale, sends, or publishes. The physical DB binding is the M6-OD-011 integration step.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.measurement.scale.models import AdsScaleRequest


class ScaleRequestStoreViolation(Exception):
    """Raised on a forbidden op (duplicate create / unknown update)."""


class ScaleRequestStore:
    def __init__(self) -> None:
        self._by_id: Dict[str, AdsScaleRequest] = {}
        self._order: List[str] = []
        self._history: List[AdsScaleRequest] = []   # append-only lifecycle trail

    def create(self, request: AdsScaleRequest) -> AdsScaleRequest:
        if request.request_id in self._by_id:
            raise ScaleRequestStoreViolation(f"scale_request {request.request_id} already exists")
        self._by_id[request.request_id] = request
        self._order.append(request.request_id)
        self._history.append(request)
        return request

    def update_state(self, request: AdsScaleRequest) -> AdsScaleRequest:
        """Persist a lifecycle transition (a NEW frozen record with the same request_id). Append-only history."""
        if request.request_id not in self._by_id:
            raise ScaleRequestStoreViolation(f"cannot update unknown scale_request {request.request_id}")
        self._by_id[request.request_id] = request
        self._history.append(request)
        return request

    def get(self, request_id: str) -> Optional[AdsScaleRequest]:
        return self._by_id.get(request_id)

    def all(self) -> Tuple[AdsScaleRequest, ...]:
        return tuple(self._by_id[i] for i in self._order)

    @property
    def history(self) -> Tuple[AdsScaleRequest, ...]:
        return tuple(self._history)

    def __len__(self) -> int:
        return len(self._order)
