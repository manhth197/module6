# EXECUTION_PLAN — Module 6 build pack

## Phase map (prompt bands)

| Band | Prompts | Gate at end | Purpose |
|---|---|---|---|
| BOOTSTRAP | M6-P0000..P0011 | Bootstrap Gate Judge (M6-P0011) | Session safety, pack integrity, state init, baselines |
| DOC_LOCK | M6-P0100..P0113 | DOC_LOCK Gate Judge (M6-P0113) | Lock precedence, boundary, rules, fail gates, smokes, contracts, decisions, lexicon |
| PHASE0_RESEARCH | M6-P0200..P0211 + critics M6-PC0200..PC0211 | (pairwise critics) | One facet per prompt; every research output adversarially reviewed |
| PHASE0 design | M6-P0300..P0309 | Phase-0 Judge (M6-P0309) | Architecture baseline, test strategy, repo audit plan |
| CONTRACT_HARMONIZATION | M6-P0700..P0715 | Harmonization Judge (M6-P0715) | Field-level schema for every MISSING contract row |
| Slice bands ×11 | M6-P1000.. (10 per slice) | Slice Gate Judge per slice | entry judge -> plan -> implement -> test build -> test run -> boundary -> security -> evidence -> docs -> judge |
| PR/PILOT | M6-P3000..P3011 | Final Review Judge | E2E chain, owner packet, pilot readiness, flag-still-OFF verification, post-pilot scale gate |

Slice order (M6-OD-010, sequential): A, B, C, D, E, F, G, H, I, J, K.

## Dependency policy

DependsOn forms a DAG with no forward references. The index CSV `DependsOn`
column and each prompt's `<required_previous_prompts>` are generated from the
SAME table by `scripts/gen_prompts.py`; `scripts/validate_registry.py` fails
if they ever diverge. Judges depend on every prompt of their band.

## Blocking decisions

Only two things may pause generation-time work: none currently. Execution-time
blocks: OPEN owner decisions (see DECISION_REGISTER "Blocks" column) block the
specific legs listed, never the whole pack.

## Context budget

Executors read: brief + active prompt + scoped slice/registers (~2–4k lines
max). Full-SPEC reads are limited to DOC_LOCK/analysis prompts. Prompts embed
their acceptance checks so executors rarely need wider context.
