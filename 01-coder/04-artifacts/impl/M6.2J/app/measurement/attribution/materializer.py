"""M6-CTR-023 attribution_materializer — materialize the attribution snapshot into Zone B (SET-ONCE).

`materialize(event, conversion, signals=...)` resolves the `ads_attribution_context` (CTR-002) and writes it, with
`revenue_value` ONLY when the conversion is ORDER_VERIFIED (RULE-003), SET-ONCE into Zone B of the measurement row
(RULE-008). It is idempotent (a re-run with the same inputs is a no-op — the resolver and store are deterministic).
A LOW / conflicting snapshot is materialized (revenue is still recorded, SMK-007) but flagged NOT scale evidence
(RULE-009). No attribution model is scale-authoritative (M6-OD-005 OPEN -> config.SCALE_MODEL_RATIFIED False;
fail-closed). No commission is ever computed (RULE-019). No order state is written, no Core override (FAIL-004).

A post-verify correction goes through `request_adjustment(...)` — an audited `AdjustmentRecord`, NEVER a direct
row rewrite (the store's set-once guard also refuses one). Nothing here sends or scales.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Tuple

from app import config
from app.measurement.attribution.adjustment import AdjustmentLog, AdjustmentRecord
from app.measurement.attribution.resolver import AttributionResolver
from app.measurement.models.attribution_context import AdsAttributionContext

_ORDER_VERIFIED = "ORDER_VERIFIED"


@dataclass(frozen=True)
class MaterializeOutcome:
    """The materializer's result — the resolved snapshot + whether it changed the row + the two fail-closed scale
    facets (data-quality eligibility, and the owner-ratified scale-evidence flag)."""

    event_id: str
    context: AdsAttributionContext
    revenue_value: Optional[float]
    changed: bool
    scale_evidence_eligible: bool     # RULE-009 data-quality bar (HIGH + NONE)
    scale_evidence: bool              # eligible AND an owner-ratified model (M6-OD-005) — always False while OPEN


class AttributionMaterializer:
    def __init__(
        self,
        store: Any,                              # MeasurementEventStore (owns the set-once Zone-B write)
        resolver: Optional[AttributionResolver] = None,
        audit: Any = None,
        *,
        verified_event_codes: Tuple[str, ...] = (_ORDER_VERIFIED,),
    ) -> None:
        self._store = store
        self._resolver = resolver or AttributionResolver()
        self._audit = audit
        self._verified = frozenset(verified_event_codes)

    def materialize(
        self,
        event: Any,
        conversion: Any,
        *,
        signals: Optional[Mapping[str, Any]] = None,
    ) -> MaterializeOutcome:
        context = self._resolver.resolve(event, conversion, signals=signals)

        # Revenue ONLY from ORDER_VERIFIED (RULE-003). A non-verified conversion materializes attribution with NO
        # revenue and NO order_code — quote/cart/draft/waiting never carry revenue (FAIL-001).
        verified = getattr(conversion, "event_code", None) in self._verified
        revenue = getattr(conversion, "revenue_value", None) if verified else None
        order_code = getattr(conversion, "order_code", None) if verified else None

        result = self._store.materialize(
            getattr(event, "event_id"),
            attribution_context=context.as_stored(),
            revenue_value=revenue,
            order_code=order_code,
            verified=verified,
        )

        # Scale-evidence facets — BOTH fail-closed (RULE-009 + M6-OD-005). A LOW/HOLD or conflicting snapshot is
        # never eligible; and even an eligible one is not scale evidence until an owner ratifies a model.
        eligible = context.is_scale_evidence_eligible()
        scale_evidence = eligible and config.SCALE_MODEL_RATIFIED

        if self._audit is not None:
            self._audit.record(
                "MATERIALIZE" if result.changed else "IDENTITY_RESOLVE",
                "ATTRIBUTION_MATERIALIZED" if result.changed else "ATTRIBUTION_MATERIALIZE_NOOP",
                subject=getattr(event, "guest_id", None) or getattr(event, "customer_id", None),
                detail=(
                    f"event={getattr(event, 'event_id', None)};verified={verified};"
                    f"confidence={context.source_confidence.value};conflict={context.conflict_status.value};"
                    f"scale_eligible={eligible};scale_evidence={scale_evidence}"
                ),
            )

        return MaterializeOutcome(
            event_id=getattr(event, "event_id"),
            context=context,
            revenue_value=result.row.revenue_value,
            changed=result.changed,
            scale_evidence_eligible=eligible,
            scale_evidence=scale_evidence,
        )

    def request_adjustment(
        self,
        event_id: str,
        *,
        actor: str,
        reason: str,
        audit_ref: str,
        evidence_ref: str,
        proposed: Mapping[str, Any],
        adjustment_log: AdjustmentLog,
        at: Optional[datetime] = None,
    ) -> AdjustmentRecord:
        """The ONLY sanctioned post-verify correction (RULE-008, SMK-018): record an audited `AdjustmentRecord` —
        it NEVER mutates the verified row. The original verified revenue/attribution is preserved unchanged; the
        adjustment is an auditable overlay. Returns the appended record."""
        record = AdjustmentRecord(
            event_id=event_id,
            actor=actor,
            reason=reason,
            audit_ref=audit_ref,
            evidence_ref=evidence_ref,
            proposed=dict(proposed),
            at=at,
        )
        adjustment_log.append(record)
        if self._audit is not None:
            self._audit.record(
                "HOLD", "ATTRIBUTION_ADJUSTMENT_RECORDED",
                subject=actor,
                detail=f"event={event_id};reason={reason};audit_ref={audit_ref}",
            )
        return record
