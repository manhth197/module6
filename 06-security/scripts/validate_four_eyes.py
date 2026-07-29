#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_four_eyes.py -- judge independence (four-eyes) over the registry.

Ported from D:/M5/Module5-workspace/scripts/m5_validate_four_eyes.py; the M5
version keys off provenance ratification records, M6 has none, so this asserts
independence statically from the locked registry and, when real evidence
exists, from recorded author identities.

STATIC (always runs, read from 00-spec/PROMPT_INDEX_LOCKED.csv -- never the
04-artifacts/state ledger; validate_registry pins index==ledger for every
static column, so the index is a faithful source and this stays off the
operator-only state path):
  For every JUDGE_GATE row R:
    * R.Agent must be the judge agent 'm6-judge' -- a judge gate is operated by
      the judge, never by a producer.
    * For every DIRECT dependency D that is production work under review
      (D is NOT itself a JUDGE_GATE row), R.Agent must differ from D.Agent:
      a judge must not sign off its own production.
    * Dependencies that are themselves JUDGE_GATE rows are prior gate
      milestones (a gate-of-gates legitimately follows an earlier judge gate),
      not production under review, so they are excluded from the agent-diff
      comparison. There is a single judge agent, so comparing against them
      would be a false positive.
    * Every dependency id must resolve in the registry (fail closed otherwise).

IDENTITY (defensive; only bites once real evidence lands, vacuous on a pristine
pack): for every JUDGE_GATE row R, if its judge sign-off file (ExpectedJudge)
is on disk, parses to a JSON object, and carries an author/operator identity,
then for every production dependency D whose evidence file (ExpectedEvidence)
is on disk and carries an author/operator identity, the two identities must
differ (casefolded). The judge who signs off must not be the operator who
produced the reviewed work. The evidence schema the gate reads is authorless,
so a missing identity field simply means the comparison cannot run (skip, do
not fail); a present-but-unreadable file fails closed.

On the pristine pack this PASSES by construction: all JUDGE_GATE rows are
m6-judge, no production dependency is m6-judge, and no evidence/sign-off files
exist yet. Read-only; writes nothing.

Print 'validate_four_eyes: PASS/FAIL (...)'; exit 0 clean / 2 with findings.
"""
import csv, json, os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
INDEX = os.path.join(ROOT, "00-spec", "PROMPT_INDEX_LOCKED.csv")

JUDGE_AGENT = "m6-judge"
JUDGE_GATE = "JUDGE_GATE"

# Author/operator identity field names probed in evidence + sign-off JSON,
# ordered by specificity; the first non-blank string value wins. These are
# optional: the gate's evidence schema records no author, so absence means the
# identity comparison cannot run for that file (skip, never fail on absence).
IDENTITY_KEYS = ("operator_or_session_id", "operator_id", "operator",
                 "author_operator", "author_id", "author", "actor",
                 "signed_by", "produced_by", "session_id", "identity_id")
# Shallow container objects that may wrap the identity fields above.
IDENTITY_CONTAINERS = ("provenance", "author", "operator", "identity", "signer")

problems = []


def bad(m):
    problems.append(m)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json_object(abs_path):
    """(obj_or_None, existed_bool). existed True + obj None => unreadable/non-object."""
    if not os.path.isfile(abs_path):
        return (None, False)
    try:
        with open(abs_path, "rb") as f:
            obj = json.loads(f.read().decode("utf-8-sig"))
    except (OSError, ValueError, UnicodeDecodeError):
        return (None, True)
    if not isinstance(obj, dict):
        return (None, True)
    return (obj, True)


def _first_identity(d):
    if not isinstance(d, dict):
        return ""
    for k in IDENTITY_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().casefold()
    return ""


def extract_identity(obj):
    """First non-blank author/operator token (top-level, then one nesting level)."""
    ident = _first_identity(obj)
    if ident:
        return ident
    if isinstance(obj, dict):
        for c in IDENTITY_CONTAINERS:
            ident = _first_identity(obj.get(c))
            if ident:
                return ident
    return ""


def main():
    rows = read_csv(INDEX)
    by = {r["PromptId"]: r for r in rows}
    judge_rows = [r for r in rows if (r.get("GateLevel") or "") == JUDGE_GATE]
    checked_pairs = 0
    identity_pairs = 0

    for r in judge_rows:
        pid = r["PromptId"]
        agent = (r.get("Agent") or "").strip()
        if agent != JUDGE_AGENT:
            bad("%s: JUDGE_GATE agent is '%s', expected '%s' (a judge gate must be "
                "operated by the judge)" % (pid, agent, JUDGE_AGENT))

        deps = [d.strip() for d in (r.get("DependsOn") or "").split(";") if d.strip()]
        prod_deps = []
        for d in deps:
            dd = by.get(d)
            if dd is None:
                bad("%s: unknown dependency '%s' (fail closed)" % (pid, d))
                continue
            if (dd.get("GateLevel") or "") == JUDGE_GATE:
                continue  # prior judge-gate milestone, not production under review
            prod_deps.append(dd)
            dep_agent = (dd.get("Agent") or "").strip()
            checked_pairs += 1
            if dep_agent == agent:
                bad("%s: judge signs off its own production -- dependency %s has the "
                    "same agent '%s' (four-eyes violation)" % (pid, d, dep_agent))

        # --- identity check (only when sign-off + evidence files carry identity) ---
        jo_rel = (r.get("ExpectedJudge") or "").strip()
        if not jo_rel:
            continue
        jo_abs = os.path.join(ROOT, jo_rel.replace("/", os.sep))
        signoff, jo_existed = load_json_object(jo_abs)
        if jo_existed and signoff is None:
            bad("%s: judge sign-off exists but is unreadable/not a JSON object: %s "
                "(fail closed)" % (pid, jo_rel))
            continue
        if signoff is None:
            continue  # pristine: no sign-off yet -> nothing to compare
        judge_ident = extract_identity(signoff)
        if not judge_ident:
            continue  # no author/operator recorded -> cannot compare identities

        for dd in prod_deps:
            ev_rel = (dd.get("ExpectedEvidence") or "").strip()
            if not ev_rel:
                continue
            ev_abs = os.path.join(ROOT, ev_rel.replace("/", os.sep))
            evidence, ev_existed = load_json_object(ev_abs)
            if ev_existed and evidence is None:
                bad("%s: dependency %s evidence exists but is unreadable/not a JSON "
                    "object: %s (fail closed)" % (pid, dd["PromptId"], ev_rel))
                continue
            if evidence is None:
                continue
            coder_ident = extract_identity(evidence)
            if not coder_ident:
                continue
            identity_pairs += 1
            if coder_ident == judge_ident:
                bad("%s: judge sign-off author identity '%s' equals producer identity "
                    "of dependency %s (four-eyes violation)"
                    % (pid, judge_ident, dd["PromptId"]))

    if problems:
        print("validate_four_eyes: FAIL (%d)" % len(problems))
        for p in problems[:60]:
            print("  - " + p)
        sys.exit(2)
    print("validate_four_eyes: PASS (%d JUDGE_GATE rows, %d judge/producer dependency "
          "pairs independent, %d identity pairs compared)"
          % (len(judge_rows), checked_pairs, identity_pairs))


if __name__ == "__main__":
    main()
