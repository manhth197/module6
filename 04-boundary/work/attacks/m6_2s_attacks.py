"""M6.2S boundary-adversary harness (READ-ONLY analysis; prompt M6-P2705).

Attacks the staged M6.2S slice — the registry-feed reader adapter (event-registry-feed.v1, staleness-safe +
fail-closed, RELAY_V221 §2.4). In-scope fail gates M6-FAIL-007 (no-evidence / overstated readiness / self-cert /
false progress) and M6-FAIL-008 (raw secret / PII on a durable/export surface); rules RULE-001 (Core owns the event
registry — M6 never writes/invents/reconciles), RULE-014 (no raw PII), RULE-015 (no self-cert). The harness drives the
real staged code and EXECUTES every claimed breach; it flips no flag, opens no send, builds no live endpoint.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2s_attacks.py

No raw psid/phone/email literal appears in this source (PII-shaped markers are runtime-assembled via chr()).
Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (FAIL-007 false-progress/self-cert OR
FAIL-008 raw PII/secret leaks from a reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows cp1252 stdout can't encode VN text
except Exception:
    pass

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2S"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2S/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.masking import mask
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy, PII_FIELDS
from app.measurement.registry.validator import _resolve_send_policy, _resolve_sensitivity, permits_external_send
from app.measurement.adapters.registry_feed_reader import RegistryFeedReader, RegistryFeedApplyResult
from app.measurement.models.registry_feed import (
    RegistryFeedRow, RegistryFeed, PROPOSED_FEED_CONTRACT, PROPOSED_FEED_ENDPOINT,
)

OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- factories ---------------------------------------------------------------------------------------
def row(event_code="EVT_A", data_sensitivity="INTERNAL", external_send_policy="INTERNAL_ONLY",
        is_active=True, event_group=None, domain=None, updated_at=None):
    r = {"event_code": event_code, "data_sensitivity": data_sensitivity,
         "external_send_policy": external_send_policy, "is_active": is_active}
    if event_group is not None:
        r["event_group"] = event_group
    if domain is not None:
        r["domain"] = domain
    if updated_at is not None:
        r["updated_at"] = updated_at
    return r


def feed(version, *rows):
    return {"registry_version": version, "events": list(rows)}


def fresh(initial=0):
    return RegistryFeedReader(initial_version=initial)


# ===================================================================================================
# GROUP FEED — feed-level fail-closed guards (FAIL-007: no false progress, no half-apply)
# ===================================================================================================
def group_FEED():
    # FE1 — a non-Mapping feed -> feed_error:not_mapping, reader UNCHANGED.
    r = fresh()
    bad = [None, 7, "x", [1], (1,), object()]
    results = [r.apply(b) for b in bad]
    if all(not res.applied and res.reason == "feed_error:not_mapping" for res in results) \
            and r.current_registry_version() == 0 and len(r) == 0:
        record("FE1", "FAIL-007", "DEFENDED",
               "a non-Mapping feed (None/int/str/list/tuple/object) -> feed_error:not_mapping; version stays 0, no "
               "rows applied (fail-closed, never crashes).")
    else:
        record("FE1", "FAIL-007", "BREACH", f"non-Mapping feed not rejected ({[x.reason for x in results]})")

    # FE2 — bad registry_version (missing / str / float / bool True/False) -> feed_error:bad_version.
    r = fresh()
    bads = [{"events": []}, {"registry_version": "1", "events": []}, {"registry_version": 1.0, "events": []},
            {"registry_version": True, "events": []}, {"registry_version": False, "events": []}]
    if all(r.apply(b).reason == "feed_error:bad_version" for b in bads) and r.current_registry_version() == 0:
        record("FE2", "FAIL-007", "DEFENDED",
               "a bad registry_version (missing / '1' str / 1.0 float / True / False bool) -> feed_error:bad_version; "
               "a bool is explicitly excluded from int (red-team fix) so True cannot pose as version 1. Version stays 0.")
    else:
        record("FE2", "FAIL-007", "BREACH", "a bad version was accepted")

    # FE3 — bad events (missing / non-list) -> feed_error:bad_events.
    r = fresh()
    bads = [{"registry_version": 1}, {"registry_version": 1, "events": {}},
            {"registry_version": 1, "events": "x"}, {"registry_version": 1, "events": 7}]
    if all(r.apply(b).reason == "feed_error:bad_events" for b in bads) and r.current_registry_version() == 0:
        record("FE3", "FAIL-007", "DEFENDED",
               "a bad events field (missing / dict / str / int — not a list/tuple) -> feed_error:bad_events; version "
               "stays 0, nothing applied.")
    else:
        record("FE3", "FAIL-007", "BREACH", "a bad events field was accepted")

    # FE4 — a non-Mapping row inside events[] -> feed_error:row_not_mapping, NOT half-applied.
    r = fresh()
    res = r.apply(feed(1, row("EVT_A"), 7, row("EVT_B")))       # a garbage element between valid rows
    if not res.applied and res.reason == "feed_error:row_not_mapping" \
            and r.current_registry_version() == 0 and len(r) == 0:
        record("FE4", "FAIL-007", "DEFENDED",
               "a non-Mapping events[] element (an int between two valid rows) -> feed_error:row_not_mapping; parse-all-"
               "first means NOTHING is applied (version 0, 0 rows) — no AttributeError, never half-applied.")
    else:
        record("FE4", "FAIL-007", "BREACH", f"a non-Mapping row half-applied (applied={res.applied}, len={len(r)})")

    # FE5 — a row missing / blank / non-str event_code -> feed_error:missing_event_code, unchanged.
    r = fresh()
    bads = [row(event_code=None), {"data_sensitivity": "PUBLIC"}, row(event_code=""), row(event_code="   "),
            row(event_code=7)]
    reasons = [r.apply(feed(1, b)).reason for b in bads]
    if all(x == "feed_error:missing_event_code" for x in reasons) and r.current_registry_version() == 0:
        record("FE5", "FAIL-007", "DEFENDED",
               "a row with a missing / None / '' / whitespace / non-str event_code -> feed_error:missing_event_code; "
               "the REQUIRED key is strictly validated (_nonblank_str), version stays 0.")
    else:
        record("FE5", "FAIL-007", "BREACH", f"a blank event_code was accepted ({reasons})")

    # FE6 — all-or-nothing: a valid-then-garbage feed applies NOTHING (parse-all-first).
    r = fresh()
    res = r.apply(feed(1, row("OK1"), row("OK2"), row(event_code="")))    # last row invalid
    if not res.applied and r.current_registry_version() == 0 and len(r) == 0 and r.get("OK1") is None:
        record("FE6", "FAIL-007", "DEFENDED",
               "all-or-nothing: a feed whose first two rows are valid but the third has a blank event_code applies "
               "NOTHING — version stays 0, OK1/OK2 are NOT stored (the reader parses all rows before mutating state, "
               "so a partial feed never yields partial progress).")
    else:
        record("FE6", "FAIL-007", "BREACH", f"a partial feed half-applied (len={len(r)}, OK1={r.get('OK1')})")

    # FE7 — non-vacuity: a fully-valid feed (events as a tuple) DOES apply + bumps the version.
    r = fresh()
    res = r.apply({"registry_version": 1, "events": (row("EVT_A"),)})     # events as a tuple
    if res.applied and res.reason == "applied" and r.current_registry_version() == 1 and len(r) == 1:
        record("FE7", "FAIL-007", "DEFENDED",
               "non-vacuity: a fully-valid feed (events as a tuple) APPLIES, reason 'applied', version -> 1, 1 row "
               "stored — the fail-closed rejects above are genuine, not a dead reject-all.")
    else:
        record("FE7", "FAIL-007", "BREACH", f"a valid feed failed to apply ({res.reason})")


# ===================================================================================================
# GROUP STALE — staleness / no-downgrade / no-poison / monotonic (FAIL-007)
# ===================================================================================================
def group_STALE():
    # ST1 — a strictly-greater feed applies + bumps + upserts; equal/older -> stale (no downgrade).
    r = fresh()
    r.apply(feed(5, row("EVT_A", external_send_policy="INTERNAL_ONLY")))
    eq = r.apply(feed(5, row("EVT_A", external_send_policy="ALLOW_EXTERNAL")))   # equal version
    old = r.apply(feed(3, row("EVT_A", external_send_policy="ALLOW_EXTERNAL")))  # older version
    still_internal = r.get("EVT_A").external_send_policy is ExternalSendPolicy.INTERNAL_ONLY
    if eq.reason == "stale" and old.reason == "stale" and r.current_registry_version() == 5 and still_internal:
        record("ST1", "FAIL-007", "DEFENDED",
               "staleness no-downgrade: after applying version 5, a feed at version 5 (equal) -> 'stale' and a feed at "
               "version 3 (older) -> 'stale'; version stays 5 and the stored EVT_A row is NOT overwritten by the stale "
               "feed's ALLOW_EXTERNAL — a replayed/older feed cannot downgrade or flip a row.")
    else:
        record("ST1", "FAIL-007", "BREACH", f"a stale feed was applied (eq={eq.reason}, ver={r.current_registry_version()})")

    # ST2 — a malformed HIGHER-version feed does NOT bump the version (no staleness poison).
    r = fresh()
    r.apply(feed(1, row("EVT_A")))
    poison = r.apply(feed(9, row("EVT_B"), 7))                  # higher version but a garbage row
    later = r.apply(feed(9, row("EVT_B")))                      # a genuine feed at the SAME version 9
    if poison.reason == "feed_error:row_not_mapping" and r.get("EVT_B") is not None \
            and later.applied and r.current_registry_version() == 9:
        record("ST2", "FAIL-007", "DEFENDED",
               "no staleness poison: a malformed feed at version 9 (a garbage row) is rejected WITHOUT bumping the "
               "version (parse-all-first, still at 1), so a later GENUINE feed at version 9 still applies (version -> "
               "9, EVT_B stored). A malformed higher-version feed cannot shut out a real one.")
    else:
        record("ST2", "FAIL-007", "BREACH", f"staleness poisoned (poison={poison.reason}, ver={r.current_registry_version()})")

    # ST3 — delta upsert: a since_version feed does NOT drop rows it omits; updates apply; prior rows survive.
    r = fresh()
    r.apply(feed(1, row("EVT_A", external_send_policy="INTERNAL_ONLY")))
    r.apply(feed(2, row("EVT_B")))                              # delta omits EVT_A
    r.apply(feed(3, row("EVT_A", external_send_policy="BLOCKED_PII")))  # update EVT_A
    a = r.get("EVT_A"); b = r.get("EVT_B")
    if a is not None and b is not None and a.external_send_policy is ExternalSendPolicy.BLOCKED_PII and len(r) == 2:
        record("ST3", "FAIL-007", "DEFENDED",
               "delta upsert: a since_version feed that omits EVT_A does NOT drop it (EVT_A survives the version-2 "
               "delta); a version-3 update to EVT_A applies (INTERNAL_ONLY -> BLOCKED_PII) while EVT_B survives — 2 "
               "rows, no row silently lost or downgraded.")
    else:
        record("ST3", "FAIL-007", "BREACH", f"delta upsert dropped/mis-applied a row (len={len(r)}, a={a})")

    # ST4 — a de-registered event arrives as is_active=False (present-but-inactive, never dropped / false-ALLOWed).
    r = fresh()
    r.apply(feed(1, row("EVT_A", is_active=True)))
    r.apply(feed(2, row("EVT_A", is_active=False)))
    a = r.get("EVT_A")
    if a is not None and a.is_active is False:
        record("ST4", "FAIL-007", "DEFENDED",
               "a de-registered event arrives as is_active=False (present-but-inactive) — the row stays readable and "
               "flagged inactive rather than being dropped or left stale-active; fail-closed de-registration.")
    else:
        record("ST4", "FAIL-007", "BREACH", f"de-registration mis-handled (a={a})")

    # ST5 — a within-feed duplicate event_code -> last-wins, order has it once, no crash.
    r = fresh()
    res = r.apply(feed(1, row("DUP", external_send_policy="INTERNAL_ONLY"),
                       row("DUP", external_send_policy="BLOCKED_PII")))
    if res.applied and len(r) == 1 and r.get("DUP").external_send_policy is ExternalSendPolicy.BLOCKED_PII:
        record("ST5", "FAIL-007", "DEFENDED",
               "a within-feed duplicate event_code is last-wins with a single order entry (len 1, no crash) — a "
               "delta-upsert dedup by event_code; a duplicate cannot inflate the row set or corrupt ordering.")
    else:
        record("ST5", "FAIL-007", "NOTE", f"within-feed dup behaviour (len={len(r)}, res={res.reason})")

    # ST6 — version edges: version 0 / negative <= initial 0 -> stale; a huge version applies once.
    r = fresh()
    zero = r.apply(feed(0, row("EVT_A")))
    neg = r.apply(feed(-5, row("EVT_A")))
    huge = r.apply(feed(10**18, row("EVT_A")))
    if zero.reason == "stale" and neg.reason == "stale" and huge.applied and r.current_registry_version() == 10**18:
        record("ST6", "FAIL-007", "DEFENDED",
               "version edges: version 0 and -5 are <= the initial 0 -> 'stale' (no apply, no negative version stored); "
               "a huge version (1e18) applies once and becomes current — the monotonic guard is a plain <= over ints.")
    else:
        record("ST6", "FAIL-007", "NOTE", f"version-edge behaviour (zero={zero.reason}, neg={neg.reason}, huge={huge.applied})")


# ===================================================================================================
# GROUP RESOLVE — fail-closed token resolution (FAIL-007 / RULE-018; no core-policy override)
# ===================================================================================================
def group_RESOLVE():
    # RS1 — unknown / None / blank / non-str external_send_policy -> BLOCKED_DEFAULT (never ALLOW_EXTERNAL).
    r = fresh()
    tokens = ["MAYBE", "", "   ", "allow", "ALLOW", "true", None, 7, object(), []]
    r.apply(feed(1, *[row(f"E{i}", external_send_policy=t) for i, t in enumerate(tokens)]))
    all_blocked = all(r.get(f"E{i}").external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT
                      for i in range(len(tokens)))
    direct = all(_resolve_send_policy(t) is ExternalSendPolicy.BLOCKED_DEFAULT for t in tokens)
    if all_blocked and direct:
        record("RS1", "FAIL-007", "DEFENDED",
               "every unknown / None / blank / whitespace / non-str external_send_policy token "
               "('MAYBE'/'allow'/'ALLOW'/'true'/None/7/object/[]) coerces to BLOCKED_DEFAULT — never a fabricated "
               "ALLOW_EXTERNAL. A near-miss casing ('allow'/'ALLOW') does not become the real member.")
    else:
        record("RS1", "FAIL-007", "BREACH", "an unknown external_send_policy escaped BLOCKED_DEFAULT")

    # RS2 — unknown / None / M3 'SENSITIVE' data_sensitivity -> PII (most restrictive); valid tokens map through.
    r = fresh()
    pii_tokens = ["SENSITIVE", "unknown", None, 7, "", "pii"]
    r.apply(feed(1, *[row(f"S{i}", data_sensitivity=t) for i, t in enumerate(pii_tokens)]))
    all_pii = all(r.get(f"S{i}").data_sensitivity is DataSensitivity.PII for i in range(len(pii_tokens)))
    r2 = fresh()
    r2.apply(feed(1, row("PUB", data_sensitivity="PUBLIC"), row("INT", data_sensitivity="INTERNAL")))
    valid = (r2.get("PUB").data_sensitivity is DataSensitivity.PUBLIC
             and r2.get("INT").data_sensitivity is DataSensitivity.INTERNAL)
    if all_pii and valid:
        record("RS2", "FAIL-007", "DEFENDED",
               "unknown / None / the M3 'SENSITIVE' token / '' / lowercase 'pii' data_sensitivity all coerce to PII "
               "(most restrictive — the reader never trusts an unrecognized token as less sensitive); real PUBLIC / "
               "INTERNAL tokens map through (non-vacuous). The M6 enum stays {PUBLIC,INTERNAL,PII} — no reconciliation "
               "member is invented (RULE-018).")
    else:
        record("RS2", "FAIL-007", "BREACH", f"a sensitivity escaped PII (all_pii={all_pii}, valid={valid})")

    # RS3 — is_active strict bool: only real True is active; every non-bool / False -> False.
    r = fresh()
    actives = [None, "true", "True", 1, 0, "false", [], 1.0, "1"]
    r.apply(feed(1, *[row(f"A{i}", is_active=a) for i, a in enumerate(actives)]))
    all_false = all(r.get(f"A{i}").is_active is False for i in range(len(actives)))
    r2 = fresh(); r2.apply(feed(1, row("T", is_active=True)))
    if all_false and r2.get("T").is_active is True:
        record("RS3", "FAIL-007", "DEFENDED",
               "is_active is a strict-bool ('row.get(is_active) is True'): None/'true'/'True'/1/0/'false'/[]/1.0/'1' "
               "all -> False; only a real True is active — a truthy non-bool can never activate an event.")
    else:
        record("RS3", "FAIL-007", "BREACH", "a non-bool is_active became True")

    # RS4 — valid external_send_policy tokens map through (non-vacuity).
    r = fresh()
    r.apply(feed(1, row("IO", external_send_policy="INTERNAL_ONLY"), row("BP", external_send_policy="BLOCKED_PII")))
    if (r.get("IO").external_send_policy is ExternalSendPolicy.INTERNAL_ONLY
            and r.get("BP").external_send_policy is ExternalSendPolicy.BLOCKED_PII):
        record("RS4", "FAIL-007", "DEFENDED",
               "valid tokens map through: 'INTERNAL_ONLY' -> INTERNAL_ONLY, 'BLOCKED_PII' -> BLOCKED_PII (the "
               "fail-closed coercion is real, not a dead block-all).")
    else:
        record("RS4", "FAIL-007", "BREACH", "a valid policy token failed to map")

    # RS5 — a feed row claiming ALLOW_EXTERNAL is faithfully READ (Core-owned classification) but reading opens NO
    #       egress: permits_external_send True only for ALLOW_EXTERNAL, yet EXTERNAL_SEND OFF + no reader egress method.
    r = fresh()
    r.apply(feed(1, row("ALLOW_EVT", external_send_policy="ALLOW_EXTERNAL")))
    ax = r.get("ALLOW_EVT").external_send_policy
    egress_verbs = ("send", "post", "publish", "emit", "deliver", "http", "fetch", "sync", "egress", "dispatch")
    reader_has_egress = any(hasattr(r, v) for v in egress_verbs)
    if ax is ExternalSendPolicy.ALLOW_EXTERNAL and permits_external_send(ax) is True \
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False and not reader_has_egress:
        record("RS5", "FAIL-007", "DEFENDED",
               "a feed row that Core classifies ALLOW_EXTERNAL is faithfully READ (M6 does not override the Core "
               "registry, RULE-001) and permits_external_send(ALLOW_EXTERNAL) is True — YET reading opens NO egress: "
               "the reader exposes no send/post/publish/sync verb, EXTERNAL_SEND is Final OFF and "
               "is_external_send_enabled() False (independent defense-in-depth). The permit-mapping decision is the "
               "OPEN M6-OD-003 (owner/Sếp); classifying is not sending.")
    else:
        record("RS5", "FAIL-007", "BREACH", f"ALLOW_EXTERNAL read opened an egress surface (egress={reader_has_egress})")

    # RS6 — no invented member: an unknown token yields an EXISTING fail-closed member, never a new vocabulary.
    unknown_pol = _resolve_send_policy("BRAND_NEW_TOKEN")
    unknown_sen = _resolve_sensitivity("BRAND_NEW_TOKEN")
    if unknown_pol in set(ExternalSendPolicy) and unknown_sen in set(DataSensitivity) \
            and unknown_pol is ExternalSendPolicy.BLOCKED_DEFAULT and unknown_sen is DataSensitivity.PII:
        record("RS6", "RULE-001", "DEFENDED",
               "no invented vocabulary (RULE-018): an unknown token resolves to an EXISTING member "
               "(BLOCKED_DEFAULT / PII), never a new/dynamic enum value — the reader classifies within the "
               "owner-signed enums and never expands them.")
    else:
        record("RS6", "RULE-001", "BREACH", "an unknown token produced a non-member")


# ===================================================================================================
# GROUP PII — FAIL-008 (raw secret / PII on the export surface; RULE-014)
# ===================================================================================================
def group_PII():
    import re as _re
    # P1 — to_public exports exactly the 7 governance fields; no customer-PII field NAME.
    r = fresh(); r.apply(feed(1, row("EVT_A", event_group="conversion", domain="commerce", updated_at="2026-01-01")))
    pub = r.get("EVT_A").to_public()
    expected = {"event_code", "data_sensitivity", "external_send_policy", "is_active",
                "event_group", "domain", "updated_at"}
    pii_names = {"phone", "email", "psid", "guest_id", "customer_id", "subject_ref", "token", "secret", "auth"}
    if set(pub) == expected and not (set(pub) & pii_names):
        record("P1", "FAIL-008", "DEFENDED",
               f"RegistryFeedRow.to_public exports exactly the 7 governance fields {sorted(expected)} — no "
               "customer-PII / secret / auth field NAME; enums as their string tokens. The feed is governance "
               "metadata (PII_FIELDS['EventRegistryRow'] = (), no PII-class field by contract).")
    else:
        record("P1", "FAIL-008", "BREACH", f"to_public field set unexpected ({set(pub)})")

    # P2 (KEY residual) — the free-text metadata (event_code/event_group/domain/updated_at) is echoed VERBATIM by
    #     to_public with NO masking. A neutral (>5-char, non-PII-shaped) marker demonstrates the raw echo; mask()
    #     would alter ANY value >5 chars, so a PII-shaped value (phone/email/id) in the same field would likewise
    #     export raw. (No literal PII in this source — the point is the ABSENCE of a masking choke.)
    marker = "FREETEXT" + "".join(chr(0x41 + (i % 26)) for i in range(14))            # 22-char alpha, no @/digits
    r = fresh()
    r.apply(feed(1, row("EVT_A", event_group=marker, domain=marker, updated_at=marker)))
    pub = r.rows()[0].to_public()
    blob = str(pub)
    echoed_raw = blob.count(marker) >= 3        # event_group + domain + updated_at all raw
    masks_differently = mask(marker) != marker  # a masking choke WOULD have altered a >5-char value
    if echoed_raw and masks_differently:
        record("P2", "FAIL-008", "OPEN_NONGATE",
               "F-FEED-PII: the free-text metadata fields (event_code/event_group/domain/updated_at) are echoed "
               "VERBATIM by to_public() with NO masking choke — a 22-char marker survives raw in all three fields, and "
               f"mask() WOULD have altered any value >5 chars (marker -> '{mask(marker)}'). So a contract-violating M3 "
               "feed that smuggled a PII-shaped value (a phone/email/customer-id) into event_group/domain would export "
               "it RAW too. Armed-not-fired for FAIL-008: the feed is a TRUSTED Core-owned governance source (not "
               "channel/customer data) and PII_FIELDS['EventRegistryRow']=() by contract, so these are "
               "governance-metadata-by-contract fields — not a customer-PII surface today. But the reader applies no "
               "defensive validation/masking to the untrusted-in-shape strings. Route SECURITY (M6-P2706) / owner: "
               "decide whether the reader should reject or mask a PII-shaped metadata value (defense-in-depth for the "
               "day the Core feed violates its own governance-metadata contract).")
    else:
        record("P2", "FAIL-008", "NOTE", f"free-text echo unexpected (echoed_raw={echoed_raw})")

    # P3 — no endpoint auth / secret field: the feed carries none, the reader stores none, RegistryFeed.to_public
    #      exposes only registry_version + events (no auth/header/token).
    snap = RegistryFeed(registry_version=1, rows=(r.rows()[0],))
    spub = snap.to_public()
    secret_names = {"auth", "token", "secret", "authorization", "header", "cookie", "api_key", "bearer"}
    if set(spub) == {"registry_version", "events"} and not (set(spub) & secret_names):
        record("P3", "FAIL-008", "DEFENDED",
               "no endpoint auth / secret is stored or exported: the feed shape carries no auth/token/header field, "
               "and RegistryFeed.to_public exposes only {registry_version, events} — there is no secret to leak (the "
               "live M3 client + its auth are the out-of-scope S1b seam, not built here).")
    else:
        record("P3", "FAIL-008", "BREACH", f"a secret/auth field is exported ({set(spub)})")

    # P4 — the reader + models bind NO HTTP/transport surface (no live endpoint, so no endpoint auth to leak).
    import app.measurement.adapters.registry_feed_reader as rd
    import app.measurement.models.registry_feed as rf
    transport = ("requests", "httpx", "urllib", "http", "socket", "aiohttp", "urllib3")
    present = [t for t in transport if hasattr(rd, t) or hasattr(rf, t)]
    if not present:
        record("P4", "FAIL-008", "DEFENDED",
               "the reader + feed-model modules bind NO HTTP/transport name (requests/httpx/urllib/http/socket/"
               "aiohttp) — no live M3 endpoint is built, so there is no endpoint URL / auth header / secret on any "
               "durable or export surface (FAIL-008).")
    else:
        record("P4", "FAIL-008", "BREACH", f"a transport surface is imported: {present}")


# ===================================================================================================
# GROUP RULE001 — Core-owned, no invention, no self-cert (RULE-001/018/015)
# ===================================================================================================
def group_RULE001():
    r = fresh()
    # R1 — the reader has no write/insert/invent method beyond apply(); apply only upserts feed-supplied rows.
    write_verbs = ("insert", "create", "add", "write", "put", "register", "upsert", "set", "invent", "reconcile")
    hits = [v for v in write_verbs if hasattr(r, v)]
    if not hits:
        record("R1", "RULE-001", "DEFENDED",
               "the reader exposes NO insert/create/add/write/register/reconcile verb — the only mutator is apply(), "
               "which upserts ONLY the rows a valid feed contains; M6 never writes or invents an event (RULE-001).")
    else:
        record("R1", "RULE-001", "BREACH", f"a write/invent verb is exposed: {hits}")

    # R2 — the reader never reconciles the Core enum: DataSensitivity stays {PUBLIC,INTERNAL,PII}; SENSITIVE->PII
    #      is a fail-closed coercion, not a new reconciled member.
    if {m.value for m in DataSensitivity} == {"PUBLIC", "INTERNAL", "PII"} \
            and _resolve_sensitivity("SENSITIVE") is DataSensitivity.PII:
        record("R2", "RULE-001", "DEFENDED",
               "no enum reconciliation invented: DataSensitivity is exactly {PUBLIC,INTERNAL,PII}; the M3 'SENSITIVE' "
               "token fail-closes to PII rather than minting a reconciled member — the two-enum reconciliation stays "
               "the OPEN owner/Core decision, the reader only consumes fail-closed.")
    else:
        record("R2", "RULE-001", "BREACH", "the sensitivity enum was reconciled/expanded")

    # R3 — no self-cert / no permit decision: RegistryFeedApplyResult reasons are only applied/stale/feed_error:*;
    #      the reader emits no Pass/Ready/authorized and decides no permit-mapping.
    reasons = set()
    rr = fresh()
    reasons.add(rr.apply(feed(1, row("EVT_A"))).reason)         # applied
    reasons.add(rr.apply(feed(1, row("EVT_A"))).reason)         # stale
    reasons.add(rr.apply(None).reason)                          # feed_error:*
    banned = {"PASS", "READY", "AUTHORIZED", "ALLOW", "CERTIFIED"}
    if reasons <= {"applied", "stale"} | {x for x in reasons if x.startswith("feed_error:")} \
            and not any(b in x.upper() for x in reasons for b in banned):
        record("R3", "RULE-015", "DEFENDED",
               f"no self-cert / no permit decision: the reader's result reasons are only {sorted(reasons)} "
               "(applied/stale/feed_error:*) — never Pass/Ready/Authorized/Allow; a successful apply advances the "
               "monotonic version but certifies nothing and decides no egress permit (RULE-015).")
    else:
        record("R3", "RULE-015", "BREACH", f"a self-cert-shaped reason appeared ({reasons})")

    # R4 — the PROPOSED contract carries a TODO(contract) marker; the reader does not invent a final name/shape.
    src = (IMPL / "app" / "measurement" / "models" / "registry_feed.py").read_text(encoding="utf-8")
    if "TODO(contract)" in src and PROPOSED_FEED_CONTRACT == "event-registry-feed.v1" \
            and "since_version" in PROPOSED_FEED_ENDPOINT:
        record("R4", "RULE-001", "DEFENDED",
               "the PROPOSED feed name/shape carries a TODO(contract) marker (final = chief-issued, RELAY_V221 "
               "finalization); the reader consumes the proposed shape but does not invent/finalize the contract "
               "(RULE-001/018).")
    else:
        record("R4", "RULE-001", "NOTE", "TODO(contract) marker / proposed constants unexpected")


# ===================================================================================================
# GROUP POSTURE — carried posture (FAIL-007/008)
# ===================================================================================================
def group_POSTURE():
    if (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False):
        record("REG", "FAIL-007", "DEFENDED",
               "posture immutable: BLOCKED / OFF / OFF, is_external_send_enabled() False — the registry-feed reader "
               "flipped nothing, built no live endpoint, opened no egress (reading the registry is inert).")
    else:
        record("REG", "FAIL-007", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    # N1 (CRIT-01 / CRIT-05, LOAD-BEARING) — the FAIL-008 free-text-echo residual (P2) stays armed-not-fired ONLY
    #     because to_public reaches NO durable sink: PII_FIELDS has no 'RegistryFeedRow' key AND no non-test app/
    #     module imports the reader / feed models. This is THE fact keeping P2 OPEN_NONGATE (not a live breach).
    app_dir = IMPL / "app"
    importers = []
    for f in app_dir.rglob("*.py"):
        if f.name in ("registry_feed_reader.py", "registry_feed.py"):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if ("registry_feed" in txt) or ("RegistryFeedReader" in txt) or ("RegistryFeedRow" in txt):
            importers.append(str(f.relative_to(IMPL)))
    pii_entry = "RegistryFeedRow" in PII_FIELDS
    if not importers and not pii_entry:
        record("N1", "FAIL-008", "DEFENDED",
               "CRIT-05 (load-bearing containment): NO non-test app/ module imports the reader or feed models "
               "(grep-clean across app/), and PII_FIELDS has no 'RegistryFeedRow' key — so RegistryFeedRow.to_public "
               "reaches NO durable / evidence / log sink today, and no name-keyed masker would touch it. THIS is why "
               "the P2 free-text-echo is armed-not-fired rather than a live FAIL-008 breach. Standing watch-item: it "
               "flips to a BREACH the moment any app module serializes to_public OR the live M3 seam (ENTRY-003) is "
               "wired — a value-level PII scrub + a PII_FIELDS['RegistryFeedRow'] entry must land first.")
    else:
        record("N1", "FAIL-008", "OPEN_NONGATE" if importers else "NOTE",
               f"to_public now has app consumers or a PII_FIELDS entry (importers={importers}, pii_entry={pii_entry}) "
               "— re-assess the P2 residual against the live sink.")

    # N2 (CRIT-02, NOVEL) — the MUTATION phase is NOT exception-atomic: a hash-raising event_code in the 2nd row
    #     commits the 1st row, leaves the version UNBUMPED, and raises OUT of apply() (half-apply + crash). The
    #     "all-or-nothing" claim holds for bad-row REJECTION (parse phase) but NOT for the upsert phase.
    class HashRaises(str):
        def __hash__(self):
            raise RuntimeError("hostile event_code hash")
    r = fresh()
    raised = False
    try:
        r.apply(feed(2, row("ROW_OK"), row(HashRaises("ROW_BAD"))))
    except Exception:
        raised = True
    committed_first = r.get("ROW_OK") is not None
    version_unbumped = r.current_registry_version() == 0
    if raised and committed_first and version_unbumped:
        record("N2", "FAIL-007", "OPEN_NONGATE",
               "CRIT-02 (novel, mutation-phase atomicity): the parse-all-first design defends bad-row REJECTION, but "
               "the UPSERT loop (mutate) is NOT exception-atomic — a 2nd-row event_code whose __hash__ raises commits "
               "the 1st row into _by_code/_order, leaves the version UNBUMPED (still 0), and propagates the exception "
               "OUT of apply() (no RegistryFeedApplyResult). So 'never crash / never half-apply' holds for malformed "
               "rows but NOT under a raising-key row: state is left partially mutated + apply() raised. In-process "
               "only (JSON yields a plain str whose hash never raises) -> not channel-reachable; a robustness caveat "
               "on the all-or-nothing headline. Route CODER: build the upsert into local copies of _by_code/_order "
               "and swap them + the version in one guarded block (or wrap the mutate phase fail-closed).")
    else:
        record("N2", "FAIL-007", "NOTE",
               f"mutation-phase atomicity unexpected (raised={raised}, committed_first={committed_first}, ver0={version_unbumped})")

    # N3 (CRIT-03 / S-04 / V1) — an int SUBCLASS with a hostile __le__ defeats the `<=` staleness guard: an equal /
    #     lower version applies (replay / downgrade). The guard excludes bool but does NOT canonicalize to a plain int.
    class EvilVer(int):
        def __le__(self, other):
            return False
    r = fresh(initial=100)
    res = r.apply({"registry_version": EvilVer(2), "events": [row("X")]})
    applied_lower = res.applied and r.get("X") is not None
    if applied_lower:
        record("N3", "FAIL-007", "OPEN_NONGATE",
               "CRIT-03/S-04 (finder-disagreement resolved to OPEN_NONGATE): the version guard is "
               "'isinstance(int) and not isinstance(bool)' (line 78) — it excludes bool but does NOT canonicalize, so "
               "an int SUBCLASS passes; then 'version <= self._version' (line 85) dispatches to the subclass's __le__. "
               "An EvilVer(2) with __le__ -> False makes version 2 read NOT-stale over a current 100 -> it APPLIES "
               "(a downgrade/replay) and stores the hostile object as the version. In-process only (a JSON/dict feed "
               "off the wire yields a plain int, for which the guard is correct) -> not channel-reachable; blast "
               "radius narrow (a later plain-int strictly-greater feed clears it). The CODE does not close it — only "
               "the transport does. Route CODER: canonicalize (version = int(version) or type(version) is int).")
    else:
        record("N3", "FAIL-007", "DEFENDED",
               f"int-subclass __le__ did not defeat staleness (applied_lower={applied_lower})")

    # N4 (CRIT-04, NOVEL) — event_code is stored UNTRIMMED (_nonblank_str tests strip() truthiness but returns the
    #     ORIGINAL): 'purchase ' and 'purchase' become DISTINCT keys, so a de-registration delta targeting the
    #     canonical code MISSES the padded stale-active row (a fail-open that overstates liveness).
    r = fresh()
    r.apply(feed(1, row("purchase ", is_active=True)))            # padded, active
    r.apply(feed(2, row("purchase", is_active=False)))            # canonical de-registration
    padded = r.get("purchase ")
    canon = r.get("purchase")
    if padded is not None and canon is not None and padded.is_active is True and canon.is_active is False and len(r) == 2:
        record("N4", "FAIL-007", "OPEN_NONGATE",
               "CRIT-04 (novel): event_code is stored UNTRIMMED — _nonblank_str tests value.strip() truthiness but "
               "returns the ORIGINAL string, so 'purchase ' and 'purchase' are DISTINCT _by_code keys. A later "
               "de-registration delta for 'purchase' (is_active=False) upserts a SEPARATE key and never overwrites "
               "the padded 'purchase ' row, which stays is_active=True — the snapshot holds both (len 2) and the "
               "de-registration misses the live row (a data-integrity fail-open overstating liveness). Channel-"
               "reachable in VALUE (plain JSON strings differing by whitespace) but no in-scope FAIL-007/008 trip "
               "(no egress, no durable sink). Route CHIEF/CODER (do not self-resolve, RULE-001): canonicalize the key "
               "with .strip() or reject non-canonical event_code; decide once whether event_code is a key or free text.")
    else:
        record("N4", "FAIL-007", "NOTE", f"untrimmed-event_code split unexpected (padded={padded}, canon={canon}, len={len(r)})")

    # N5 (resolve BND-01, carried M6.2P) — a hostile-__eq__/__hash__ object coerces to ALLOW_EXTERNAL / PUBLIC via the
    #     enum value2member lookup: _resolve_send_policy / _resolve_sensitivity have NO isinstance(str) gate before
    #     ExternalSendPolicy(raw) / DataSensitivity(raw), so a non-str object whose hash+eq match a member's VALUE maps.
    class HostilePolicy:
        def __hash__(self):
            return hash("ALLOW_EXTERNAL")
        def __eq__(self, other):
            return other == "ALLOW_EXTERNAL"
    class HostileSens:
        def __hash__(self):
            return hash("PUBLIC")
        def __eq__(self, other):
            return other == "PUBLIC"
    pol = _resolve_send_policy(HostilePolicy())
    sen = _resolve_sensitivity(HostileSens())
    if pol is ExternalSendPolicy.ALLOW_EXTERNAL or sen is DataSensitivity.PUBLIC:
        record("N5", "FAIL-007", "OPEN_NONGATE",
               "resolve BND-01 (carried M6.2P residual): _resolve_send_policy / _resolve_sensitivity have NO "
               "isinstance(str) gate before ExternalSendPolicy(raw) / DataSensitivity(raw), so a NON-str object whose "
               f"__hash__ + __eq__ match a member's value maps to the permissive member (send->{pol.value}, "
               f"sensitivity->{sen.value}) via the enum value2member dict lookup — defeating the fail-closed default "
               "for a crafted object. In-process code-exec ONLY (a JSON feed yields str/None/int, all handled "
               "fail-closed; a str-subclass equal to 'ALLOW_EXTERNAL' genuinely IS that value, not a bypass) -> not "
               "channel-reachable, and even coerced-ALLOW_EXTERNAL opens no egress here (EXTERNAL_SEND OFF, reader has "
               "no send verb). Route CODER: add an isinstance(raw, str) gate before the enum call (mirror-parity; "
               "carried from M6.2P).")
    else:
        record("N5", "FAIL-007", "DEFENDED",
               f"a hostile-eq object did NOT coerce to a permissive member (send={pol.value}, sensitivity={sen.value})")

    # N6 (S-08 tombstone + V2 huge-version) — two documented armed-not-fired residuals, executed as NOTEs.
    r = fresh()
    r.apply(feed(1, row("A", is_active=True)))
    r.apply(feed(2, row("B")))                                   # delta OMITS A (Core-removed-by-omission?)
    a_retained_active = r.get("A") is not None and r.get("A").is_active is True
    r2 = fresh()
    r2.apply(feed(2 ** 62, row("A")))
    pinned = r2.apply(feed(7, row("B"))).reason
    record("N6", "FAIL-007", "NOTE",
           "documented armed-not-fired residuals (route CHIEF/OWNER, not this slice): (a) S-08 tombstone-by-omission — "
           f"the upsert has NO removal path, so an event Core removes by OMITTING it from a later delta is retained at "
           f"its last-seen state (A still present + is_active={a_retained_active}); if Core signals de-registration by "
           "dropping the row rather than resending is_active=False, M6 overstates liveness. TODO(contract) already "
           "flags tombstone semantics as chief-owned. (b) V2 huge-version staleness-pin — a valid huge version "
           f"(2**62) applies once, then a later genuine feed at version 7 is '{pinned}' forever (monotonic <= is a "
           "denial-of-progress / availability concern, not an in-scope FAIL gate; reachable only via the authorized "
           "fully-valid apply path). Route owner/contract: bound the version range / define tombstone semantics.")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2S BOUNDARY ADVERSARY — registry-feed reader (in-scope: FAIL-007 / FAIL-008)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_FEED, group_STALE, group_RESOLVE, group_PII, group_RULE001, group_POSTURE, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-007", "FAIL-008", "RULE-001", "RULE-014", "RULE-015")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE BREACHES (FAIL-007 / FAIL-008 / RULE-001/014/015): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
