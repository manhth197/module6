"""Learning layer (M6.2H): the six ADS Strategy Libraries + the learning-engine skeleton (Seed → Run → Learn →
Review → Publish, doc §17).

Guarded learning (RULE-011, LEX-006 — the doc's FORBIDDEN cell): the machine NEVER fabricates origin strategy.
Each library seeds ONLY from its canonical source; content fill HALTS at framework while M6-OD-007 is OPEN
(`LEARNING_CONTENT_FILL_ENABLED=False`). The Learn stage runs ONLY after a canonical seed exists and consumes ONLY
verified business signals that passed the Data Quality Gate. Candidates land in a review queue; there is NO
auto-publish path — publish is owner-approval-only, and the guarded safe-range publish is BLOCKED while M6-OD-006
is OPEN (`LEARNING_SAFE_RANGE_RATIFIED=False`, FAIL-006). Nothing generates public ad copy, nothing publishes.
"""
