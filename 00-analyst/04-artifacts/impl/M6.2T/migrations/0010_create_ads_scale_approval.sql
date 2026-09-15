-- Migration 0010 — create ads_scale_approval (M6-CTR-026 Scale-Gate approval flow, owner-decision records)
-- STAGED per 04-artifacts/state/IMPLEMENTATION_TARGET_LOCKED.json (live_migrations=false): NEVER applied here.
--
-- One row per explicit OWNER decision on a scale request (append-only). Every decision carries actor + reason +
-- audit_ref + evidence_ref (RULE-015 — the system never synthesizes an approval). RULE-010 / FAIL-006: recording
-- an APPROVE decision here NEVER triggers a scale — it is an audit record of the owner's decision; the owner
-- performs any budget change OUTSIDE Module 6 (production_flag=OFF). An APPROVE is only recorded after the Risk row
-- (RULE-017) is re-checked clear at approval time and a budget_cap + rollback_condition exist. Applies AFTER 0009.

-- ============================================================ UP
CREATE TABLE ads_scale_approval (
    approval_id   TEXT NOT NULL PRIMARY KEY,
    request_id    TEXT NOT NULL,                       -- FK -> ads_scale_request.request_id
    decision      TEXT NOT NULL,                       -- APPROVE | REJECT
    actor         TEXT NOT NULL,                       -- owner/operator id (masked in logs/evidence, RULE-014)
    reason        TEXT NOT NULL,
    audit_ref     TEXT NOT NULL,
    evidence_ref  TEXT NOT NULL,
    decided_at    TIMESTAMP NOT NULL,
    CONSTRAINT fk_asa_request FOREIGN KEY (request_id) REFERENCES ads_scale_request (request_id),
    CONSTRAINT ck_asa_decision CHECK (decision IN ('APPROVE','REJECT'))
);

CREATE INDEX ix_asa_request_id ON ads_scale_approval (request_id);

-- No trigger/rule ever attached: recording an APPROVE here does not raise a budget, enable a campaign, or open
-- audience scale (RULE-010). This is the owner-approval AUDIT trail for the Scale-Gate proposal.

-- ============================================================ DOWN (rollback)
-- Staged now => documented, not executed.
-- DROP TABLE ads_scale_approval;
