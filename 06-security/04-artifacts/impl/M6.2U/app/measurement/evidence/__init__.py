"""M6.2K Smoke & Evidence Pack — the owner sign-off package assembler (STAGED, assembly-only).

Re-runs the full P0 smoke matrix (the TESTER executes; this layer registers + reports) and assembles the doc §22
evidence plan (10 categories) into an owner review package with an HONEST gap/blocker list. It NEVER declares ROAS
Pass / Scale Ready (owner-only, doc §23), NEVER self-certifies (RULE-015), and a missing evidence category / un-run
smoke ⇒ NOT_READY (fail-closed, FAIL-007). No new table (RULE-018), no flag flip, no raw PII (RULE-014). Readiness
tops out at OWNER_REVIEW_REQUIRED.
"""
