"""M6.2Q ads-spend materialize worker (A5, M6-OD-016) — the drain that turns APPROVED imports into spend records.

`run_once()` selects APPROVED-and-not-yet-materialized imports and writes each CSV row SET-ONCE into the record
store as a CAMPAIGN-LEVEL AdsSpendRecord (campaign_id + amount + spend_date; adset_id / ad_id are None — the phase-1
source is campaign-level, M6-OD-016). A PROPOSED / REJECTED import materializes NOTHING (fail-closed): only an
APPROVED import — one a DISTINCT checker approved — is ever materialized. Nothing is sent; no network is touched.
Mirrors the outbox drain-loop (`run_once`) + the set-once destination store precedent.
"""
from __future__ import annotations

from typing import Any, List

from app.measurement.dashboard.data_mart import AdsSpendRecord
from app.measurement.models.ads_spend_import import AdsSpendImportState
from app.measurement.store.ads_spend_import_store import AdsSpendImportStore
from app.measurement.store.ads_spend_record_store import AdsSpendRecordStore


class AdsSpendMaterializer:
    def __init__(self, import_store: AdsSpendImportStore, record_store: AdsSpendRecordStore, audit: Any = None) -> None:
        self._imports = import_store
        self._records = record_store
        self._audit = audit

    def run_once(self) -> List[str]:
        """Drain APPROVED imports into set-once spend records. Returns the import_ids materialized this pass
        (non-APPROVED and already-materialized imports are skipped). Idempotent: a re-run materializes nothing new."""
        done: List[str] = []
        for imp in self._imports.all():
            if imp.state is not AdsSpendImportState.APPROVED:
                continue                                  # fail-closed: only an APPROVED import materializes
            if self._records.is_materialized(imp.import_id):
                continue                                  # already drained (idempotent)
            records = tuple(
                AdsSpendRecord(
                    amount=row.spend_value,
                    campaign_id=row.campaign_id,          # campaign-level (M6-OD-016): adset_id / ad_id stay None
                    spend_date=row.spend_date,
                )
                for row in imp.rows
            )
            self._records.materialize_import(imp.import_id, records)
            done.append(imp.import_id)
            if self._audit is not None:
                self._audit.record(
                    "HOLD", "ADS_SPEND_IMPORT_MATERIALIZED", subject=imp.decided_by,
                    detail=f"import={imp.import_id};rows={len(records)}",
                )
        return done
