"""Official smoke — slice M6.2B — M6-SMK-003 (doc ADS-P0-003).

Authored by TESTER in M6-P1103 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 403):

    Kịch bản (verbatim):          "Duplicate Pixel/CAPI/Offline"
    Kết quả phải đạt (verbatim):  "Dedup, không double count"

M6.2B proves the dedup CAPABILITY on the tracking pipeline: a duplicate track request is collapsed by the
LOCKED RULE-005 idempotency key, which the endpoint derives SERVER-SIDE from a canonicalization of the raw body
(excluding the volatile `idempotency_key`/`correlation_id`), so a replay maps to the same key. The dedup holds
end-to-end in BOTH append-only stores — the raw `web_event_logs` (RULE-007) and the normalized
`ads_measurement_events` (UNIQUE idempotency_key, RULE-005) — so a replay never double counts. (The full
cross-source Pixel/CAPI/Offline dedup by content is exercised again where those channels are wired, M6.2D;
M6.2B's manifestation is the exact-replay dedup on the track endpoint.) RULE-005 / RULE-007. All ids synthetic;
no raw PII. Reuses the shared conftest fixtures (`track_deps`, `make_track_body`, `store`, `measurement_store`).
"""
from __future__ import annotations

from app.api.track import handle_track_request


# --- primary smoke: scenario verbatim, end-to-end through the track endpoint -----------------------
def test_smk_003_duplicate_event_is_deduped_no_double_count(
    track_deps, make_track_body, store, measurement_store
):
    """M6-SMK-003 "Duplicate Pixel/CAPI/Offline" -> "Dedup, không double count".

    An identical track request replayed is collapsed by the server-derived RULE-005 idempotency key: the first
    is ACCEPTED, the replay is DUPLICATE (idempotent_replay) mapping to the SAME normalized event, and each
    append-only store holds exactly one row — no double count.
    """
    body = make_track_body()
    first = handle_track_request(body, track_deps)
    second = handle_track_request(dict(body), track_deps)   # identical duplicate replayed

    assert first.status == "ACCEPTED" and first.idempotent_replay is False
    assert second.status == "DUPLICATE" and second.idempotent_replay is True
    assert second.event_id == first.event_id, "a replay maps to the same normalized event, not a new one"
    assert len(store) == 1, "no second web_event_logs row (RULE-005/007, không double count)"
    assert len(measurement_store) == 1, "no second ads_measurement_events row (RULE-005, SMK-003)"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_003_neg_replay_with_a_different_correlation_id_still_dedupes(
    track_deps, make_track_body, store, measurement_store
):
    """The RULE-005 key excludes the volatile `correlation_id`, so a replay carrying a fresh trace id still
    dedups — dedup keys on the event's identity, not on the caller's trace id."""
    handle_track_request(make_track_body(correlation_id="corr_A"), track_deps)
    second = handle_track_request(make_track_body(correlation_id="corr_B"), track_deps)
    assert second.status == "DUPLICATE" and second.idempotent_replay is True
    assert len(store) == 1 and len(measurement_store) == 1


def test_smk_003_neg_repeated_replays_never_double_count(
    track_deps, make_track_body, store, measurement_store
):
    """Idempotent under repeated replay: many replays of the same event still leave exactly one row per store."""
    body = make_track_body()
    results = [handle_track_request(dict(body), track_deps) for _ in range(3)]
    assert results[0].status == "ACCEPTED" and results[0].idempotent_replay is False
    assert all(r.status == "DUPLICATE" and r.idempotent_replay is True for r in results[1:])
    assert len(store) == 1 and len(measurement_store) == 1


# --- positive control: proves dedup DISCRIMINATES (does not collapse distinct events) --------------
def test_smk_003_control_distinct_event_is_not_deduped(
    track_deps, make_track_body, store, measurement_store
):
    """Control (non-vacuity): a genuinely different event (different page_id -> different RULE-005 key) is NOT
    deduped — it is a fresh ACCEPTED row in each store. Proves the dedup collapses true duplicates only, not
    everything."""
    handle_track_request(make_track_body(), track_deps)                       # VIEW_LANDING, page p1
    other = handle_track_request(make_track_body(page_id="p2"), track_deps)   # different page -> different key
    assert other.status == "ACCEPTED" and other.idempotent_replay is False
    assert len(store) == 2 and len(measurement_store) == 2
