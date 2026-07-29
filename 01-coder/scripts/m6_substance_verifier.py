#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
m6_substance_verifier.py -- M6 gate hardening: the SUBSTANCE verifier.

The M6 locked gate (scripts-win/Check-PromptGateLocked.ps1) validates the
SHAPE of evidence (keys present, prompt_id match, status pass-like,
fail_gate_tripped=false, open_blockers empty, refs exist, ...). It TRUSTS the
author-declared verdict fields. This verifier converts that trust into
verification:

  - The author-declared fields (status, fail_gate_tripped, open_blockers) are
    ADVISORY.
  - The verifier RECOMPUTES the fail-gate verdict from the severity / blocker
    signals actually recorded across the evidence sibling keys (open_blockers,
    findings[] severities, test_results[] results, fail_gate_lines,
    fail_gate_tripped). That computed verdict is AUTHORITATIVE.
  - A claimed-vs-computed MISMATCH (author says fail_gate_tripped=false while
    the recomputed verdict trips) is itself a FAIL -- an integrity violation
    (maps to M6-FAIL-009 Gate bypass in 00-spec/registers/FAIL_GATE_REGISTER.md).

Severity tokens map to the M6 FAIL_GATE_REGISTER: a recorded P0 / SEV0 / S0 /
BLOCKER / CRITICAL finding (or a non-empty open_blockers list, or a FAILED /
BLOCKED test result, or non-empty fail_gate_lines) trips the gate. HIGH and
below stay advisory by design, mirroring the hardened M5 verifier.

Anti-dodge (ported from M5): severity is read across a set of sibling keys
(severity / sev / level / priority / ...), NFKC-normalized, homoglyph-folded
(Cyrillic / Greek look-alikes -> Latin), uppercased and stripped to A-Z0-9,
so a critic cannot hide a P0 under 'level' or spell it with a Cyrillic 'C'.

Fresh pack: STRICT from Order 1 -- there is no epoch / grandfather list. The
EPOCH_REGISTER_REL seam below is left as a clearly marked extension point so an
epoch register can be added later without reworking the recompute.

Vacuous pass: when there is NO evidence yet (file missing / empty /
unparseable), presence and parse are the SHAPE gate's responsibility (it
Add-Fails already), so the substance verifier defers and returns a clean
vacuous pass (exit 0, computed_status NO_EVIDENCE). It only produces substance
failures when it holds a parseable evidence object. This is what lets the
verifier PASS cleanly on the pristine pre-run pack.

CLI:
  python scripts/m6_substance_verifier.py --mode gate --prompt <ID> [--root .]
        [--ledger <ws-rel-path>] [--write-computed] [--caller gate] [--json]

  --caller gate : emit ONLY the single JSON object on stdout (gate parses it),
                  and suppress every human/stderr line (so a stderr write under
                  the caller's $ErrorActionPreference='Stop' + 2>&1 capture
                  cannot terminate the gate).
  --json        : force the JSON object on stdout for a manual run.
  (default)     : print a human "m6_substance_verifier: PASS/FAIL (...)" line.

Exit codes: 0 pass (clean or vacuous); 2 substance failure(s) / integrity
violation; 3 internal error (fail-closed).

Stdlib only. Python >= 3.11. CSV read utf-8-sig; JSON/text read utf-8 (BOM
tolerated). Evidence key access is CASE-INSENSITIVE (PowerShell-gate parity).
Evidence schema is minimum-keys: unknown keys are NEVER rejected. ASCII-only
source literals (confusable code points are given as hex, built into the map at
import). No emails.
"""

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys
import unicodedata

RULES_VERSION = "M6-SGV-1.0"
DEFAULT_LEDGER_REL = "04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv"
# Extension seam (fresh pack: strict from Order 1, so this register does not
# exist yet). Drop a JSON register here later to grandfather specific rows.
EPOCH_REGISTER_REL = "00-spec/registers/M6_SUBSTANCE_GATE_EPOCH.json"
COMPUTED_DIR_REL = "04-artifacts/gate-hardening/computed"
EVIDENCE_DIR_REL = "04-artifacts/evidence/prompts"

# Sibling keys that may carry a finding's severity. Scanned so that a critic
# cannot dodge the trip by moving severity off 'severity' onto 'level' / 'sev'
# / 'priority' / etc.
SEVERITY_KEYS = ("severity", "sev", "level", "priority", "severity_level", "sev_level")

# Test-result values that trip the fail gate. M6 evidence uses the key 'result'
# (smoke_id/result/detail); 'status' is also accepted for robustness.
TRIP_TEST_RESULTS = frozenset({"FAIL", "FAILED", "BLOCKED", "ERROR"})

# Status values the gate treats as pass-like (mirrors _M6RunnerLib PassLike).
PASS_LIKE = frozenset({"PASS", "SIGNED", "SKIPPED"})

REQUIRED_BASE_KEYS = (
    "prompt_id",
    "status",
    "summary",
    "files_read",
    "files_changed",
    "commands_run",
    "evidence_refs",
    "open_blockers",
    "fail_gate_tripped",
    "fail_gate_lines",
    "next_recommended_action",
)

# Confusable homoglyphs -> Latin. NFKC does NOT fold Cyrillic / Greek letters
# that merely LOOK like Latin ones, so the documented evasion set is mapped
# explicitly. Given as (codepoint, latin) pairs to keep this source ASCII-only
# per the M6 house rule; the runtime keys are the real confusable characters.
# (codepoint, latin) pairs -- source stays ASCII via hex codepoints; the
# runtime keys are the real Cyrillic / Greek confusable characters.
_CONFUSABLE_PAIRS = (
    (0x0421, "C"),  # Es
    (0x0420, "P"),  # Er
    (0x0410, "A"),  # A
    (0x041E, "O"),  # O
    (0x0415, "E"),  # Ie
    (0x0412, "B"),  # Ve
    (0x041C, "M"),  # Em
    (0x041D, "H"),  # En (looks like H)
    (0x041A, "K"),  # Ka
    (0x0422, "T"),  # Te
    (0x0425, "X"),  # Ha
    (0x0406, "I"),  # Byelorussian-Ukrainian I
    (0x0405, "S"),  # Dze (looks like S)
    (0x0441, "C"),  # es
    (0x0440, "P"),  # er
    (0x0430, "A"),  # a
    (0x043E, "O"),  # o
    (0x0435, "E"),  # ie
    (0x0432, "B"),  # ve
    (0x0445, "X"),  # ha
    (0x0456, "I"),  # i
    (0x0455, "S"),  # dze
    (0x0391, "A"),  # Alpha
    (0x039F, "O"),  # Omicron
    (0x0392, "B"),  # Beta
    (0x0395, "E"),  # Epsilon
    (0x0396, "Z"),  # Zeta
    (0x0397, "H"),  # Eta
    (0x039A, "K"),  # Kappa
    (0x039C, "M"),  # Mu
    (0x039D, "N"),  # Nu
    (0x03A1, "P"),  # Rho
    (0x03A4, "T"),  # Tau
    (0x03A7, "X"),  # Chi
    (0x0399, "I"),  # Iota
    (0x03B1, "A"),  # alpha
    (0x03BF, "O"),  # omicron
)
_CONFUSABLE_MAP = {chr(cp): latin for cp, latin in _CONFUSABLE_PAIRS}

# Exact normalized tokens that trip the fail gate.
_TRIP_SEVERITY_TOKENS = frozenset({"P0", "SEV0", "S0", "BLOCKER", "CRITICAL"})
# Substrings whose presence anywhere in a normalized token trips the gate, to
# catch fused evasions (P0CRITICAL, BLOCKERP0, SEV0X, ...).
_TRIP_SEVERITY_SUBSTRINGS = ("SEV0", "BLOCKER", "CRITICAL")
# 'P0' trips when it appears in a token and is NOT immediately followed by
# another digit (so 'P01'/'P011' priority levels do NOT false-trip). A whole
# token of the form 'P0' + an exemption suffix stays advisory.
_TRIP_P0_RE = re.compile(r"P0(?!\d)")
_P0_EXEMPT_TOKENS = frozenset(
    "P0" + suffix for suffix in ("EXEMPT", "EXEMPTION", "WAIVED", "WAIVER", "NA", "NONE"))

_MISSING = object()
_SUPPRESS_INFO = False


def _info(msg):
    if _SUPPRESS_INFO:
        return
    print(msg, file=sys.stderr)


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm_rel(path):
    return (str(path) if path is not None else "").strip().replace("\\", "/")


def _abs(root, rel):
    return os.path.join(root, _norm_rel(rel).replace("/", os.sep))


def ci_get(obj, key, default=None):
    """Case-insensitive dict lookup (PowerShell ConvertFrom-Json parity)."""
    if not isinstance(obj, dict):
        return default
    if key in obj:
        return obj[key]
    low = key.lower()
    for k, v in obj.items():
        if isinstance(k, str) and k.lower() == low:
            return v
    return default


def as_list(value):
    """Normalize a scalar / None / list into a list (None -> [])."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_boolish(value):
    """True / False / 'UNKNOWN' (anything non-boolean-ish is UNKNOWN => trip)."""
    if value is _MISSING or value is None:
        return "UNKNOWN"
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low == "true":
            return True
        if low == "false":
            return False
    return "UNKNOWN"


def normalize_severity(value):
    """Fold a raw severity value to a canonical uppercase A-Z0-9 token.

    NFKC-normalize, map documented Cyrillic / Greek confusables to Latin,
    uppercase, then strip everything that is not A-Z or 0-9. Non-string values
    fold to their str(). Returns '' for empty / None.
    """
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    text = unicodedata.normalize("NFKC", text)
    text = "".join(_CONFUSABLE_MAP.get(ch, ch) for ch in text)
    text = text.upper()
    return re.sub(r"[^A-Z0-9]+", "", text)


def severity_trips(token):
    """True when a normalized severity token trips the fail gate.

    Tripping set: P0 (token or fused, but not P01 / P0-EXEMPT forms), SEV0, S0,
    BLOCKER, CRITICAL, plus any token CONTAINING SEV0 / BLOCKER / CRITICAL.
    HIGH, MEDIUM, LOW, P1, P2 and the P0-EXEMPT / P0-WAIVED tokens stay advisory.
    """
    if not token:
        return False
    if token in _P0_EXEMPT_TOKENS:
        return False
    if token in _TRIP_SEVERITY_TOKENS:
        return True
    for needle in _TRIP_SEVERITY_SUBSTRINGS:
        if needle in token:
            return True
    if _TRIP_P0_RE.search(token):
        return True
    return False


def finding_severity_token(finding):
    """Highest-severity normalized token found across SEVERITY_KEYS of a finding.

    Prefers a tripping token when any sibling key carries one (so hiding P0
    under 'level' while putting 'LOW' on 'severity' still trips); otherwise
    returns the first non-empty normalized token for diagnostics.
    """
    first_token = ""
    for key in SEVERITY_KEYS:
        token = normalize_severity(ci_get(finding, key))
        if not token:
            continue
        if not first_token:
            first_token = token
        if severity_trips(token):
            return token
    return first_token


def _find_finding_description(finding):
    for key in ("description", "summary", "detail", "title", "resolution"):
        value = ci_get(finding, key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def recompute_fail_gate(evidence):
    """(computed_fail_gate_tripped, reasons) recomputed from the evidence.

    OR of:
      - fail_gate_tripped missing / UNKNOWN / non-boolean-ish  => TRUE;
      - open_blockers non-empty (M6-FAIL-* acknowledged blocker);
      - any finding whose normalized severity trips (P0 / SEV0 / S0 / BLOCKER /
        CRITICAL and fused / homoglyph variants, scanned across SEVERITY_KEYS;
        HIGH and below are advisory by design);
      - any test_results item whose result / status is FAIL / BLOCKED / ERROR;
      - witness invariant: fail_gate_lines non-empty while the author declared
        fail_gate_tripped=false (the author recorded fail-gate evidence yet
        claimed clean).
    """
    if not isinstance(evidence, dict):
        return (True, ["evidence is not a JSON object (UNKNOWN => TRUE, fail closed)"])
    reasons = []
    claimed = parse_boolish(ci_get(evidence, "fail_gate_tripped", _MISSING))
    if claimed == "UNKNOWN":
        reasons.append("fail_gate_tripped missing/UNKNOWN/non-boolean (UNKNOWN => TRUE)")
    blockers = as_list(ci_get(evidence, "open_blockers"))
    if len(blockers) > 0:
        reasons.append("open_blockers non-empty (%d item(s))" % len(blockers))
    for index, finding in enumerate(as_list(ci_get(evidence, "findings")), start=1):
        if not isinstance(finding, dict):
            continue
        severity = finding_severity_token(finding)
        if severity_trips(severity):
            description = _find_finding_description(finding)
            reasons.append("finding #%d severity %s trips the fail gate: %s"
                           % (index, severity, description[:160]))
    for index, item in enumerate(as_list(ci_get(evidence, "test_results")), start=1):
        if not isinstance(item, dict):
            continue
        result = str(ci_get(item, "result", ci_get(item, "status")) or "").strip().upper()
        if result in TRIP_TEST_RESULTS:
            smoke_id = str(ci_get(item, "smoke_id", ci_get(item, "test_id")) or "").strip()
            reasons.append("test_results item #%d (%s) result %s trips the fail gate"
                           % (index, smoke_id or "?", result))
    lines = as_list(ci_get(evidence, "fail_gate_lines"))
    if len(lines) > 0 and claimed is False:
        reasons.append("witness invariant violated: fail_gate_lines non-empty while "
                       "fail_gate_tripped=false")
    return (len(reasons) > 0, reasons)


def _load_ledger(root, ledger_rel):
    """(rows_or_None, warnings). Ledger absence is a WARNING here, not a failure:
    presence of ledger/row is the shape gate's job; the substance verifier only
    needs the row to resolve ExpectedEvidence."""
    abs_path = _abs(root, ledger_rel)
    if not os.path.isfile(abs_path):
        return (None, ["ledger not found: %s (evidence path defaulted)" % _norm_rel(ledger_rel)])
    try:
        with open(abs_path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return (rows, [])
    except (OSError, csv.Error) as exc:
        return (None, ["ledger unreadable: %s (%s)" % (_norm_rel(ledger_rel), exc)])


def _find_row(rows, prompt_id):
    for row in rows or []:
        if str(row.get("PromptId") or "").strip() == prompt_id:
            return row
    return None


def classify_row(row):
    """Light mechanical classification (advisory only; the recompute is
    classification-agnostic). Kept for the computed record's traceability."""
    if not isinstance(row, dict):
        return "standard"
    gate_level = str(row.get("GateLevel") or "").strip().upper()
    role = str(row.get("Role") or "").strip().upper()
    if gate_level == "JUDGE_GATE" or role == "JUDGE":
        return "judge"
    if role == "TESTER":
        return "test"
    return "standard"


def verify_prompt(root, ledger_rel, prompt_id, mode):
    """Verify one prompt's evidence substance. Returns (record, exit_code)."""
    failures = []
    warnings = []
    integrity_violations = []
    evidence_sha256 = {}
    classification = "standard"
    claimed = "UNKNOWN"
    computed_tripped = False
    evidence_present = False

    rows, ledger_warnings = _load_ledger(root, ledger_rel)
    warnings.extend(ledger_warnings)
    row = _find_row(rows, prompt_id) if rows is not None else None
    if rows is not None and row is None:
        warnings.append("prompt not found in ledger: %s (evidence path defaulted)" % prompt_id)

    evidence_rel = "%s/%s.json" % (EVIDENCE_DIR_REL, prompt_id)
    if row is not None:
        expected = _norm_rel(row.get("ExpectedEvidence") or "")
        if expected:
            evidence_rel = expected
        classification = classify_row(row)
    evidence_abs = _abs(root, evidence_rel)

    # Vacuous-pass: presence / parse belong to the SHAPE gate. If there is no
    # parseable evidence, the substance verifier has nothing to recompute and
    # defers (clean exit 0). It NEVER weakens the overall gate: the shape gate
    # Add-Fails on missing / unparseable evidence in the same run.
    evidence = None
    if not os.path.isfile(evidence_abs):
        warnings.append("no evidence file yet: %s (deferred to shape checks; vacuous pass)"
                        % evidence_rel)
    else:
        try:
            with open(evidence_abs, "rb") as f:
                raw = f.read()
            evidence_sha256[evidence_rel] = hashlib.sha256(raw).hexdigest()
            text = raw.decode("utf-8-sig")
            if not text.strip():
                warnings.append("evidence file empty/whitespace: %s (deferred to shape checks)"
                                % evidence_rel)
            else:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    evidence = parsed
                    evidence_present = True
                else:
                    warnings.append("evidence is not a JSON object: %s (deferred to shape checks)"
                                    % evidence_rel)
        except UnicodeDecodeError as exc:
            warnings.append("evidence not valid utf-8: %s (%s) (deferred to shape checks)"
                            % (evidence_rel, exc))
        except (OSError, ValueError) as exc:
            warnings.append("evidence unreadable/invalid JSON: %s (%s) (deferred to shape checks)"
                            % (evidence_rel, exc))

    if evidence is not None:
        # Minimum-keys presence is the shape gate's job; here we only note a
        # missing prompt_id / status that the recompute relies on.
        declared_id = str(ci_get(evidence, "prompt_id") or "").strip()
        if declared_id and declared_id != prompt_id:
            failures.append("evidence prompt_id mismatch: declared %r expected %r (fail closed)"
                            % (declared_id, prompt_id))

        claimed = parse_boolish(ci_get(evidence, "fail_gate_tripped", _MISSING))

        # AUTHORITATIVE recompute. Author fields above are ADVISORY.
        computed_tripped, trip_reasons = recompute_fail_gate(evidence)
        if computed_tripped:
            failures.extend("computed fail gate: %s" % r for r in trip_reasons)
            # Claimed-vs-computed mismatch = integrity violation (M6-FAIL-009
            # Gate bypass): the author declared clean while the recorded
            # evidence trips the gate.
            if claimed is False:
                integrity_violations.append(
                    "CLAIMED_VS_COMPUTED_MISMATCH: fail_gate_tripped=false but recomputed "
                    "verdict trips (M6-FAIL-009 gate bypass)")

        # A pass-like status while the computed verdict trips is the same
        # integrity problem stated on the status field.
        status_value = str(ci_get(evidence, "status") or "").strip().upper()
        if computed_tripped and status_value in PASS_LIKE and claimed is not False:
            integrity_violations.append(
                "CLAIMED_VS_COMPUTED_MISMATCH: status %r is pass-like but recomputed verdict "
                "trips (M6-FAIL-009 gate bypass)" % status_value)

    if failures or integrity_violations:
        computed_status = "FAIL"
    elif not evidence_present:
        computed_status = "NO_EVIDENCE"
    else:
        computed_status = "CLEAN"

    record = {
        "prompt_id": prompt_id,
        "checked_at": _now_iso(),
        "rules_version": RULES_VERSION,
        "mode": mode,
        "classification": classification,
        "evidence_present": evidence_present,
        "computed_status": computed_status,
        "claimed_fail_gate_tripped": claimed,
        "computed_fail_gate_tripped": bool(computed_tripped) if evidence_present else False,
        "integrity_violations": integrity_violations,
        "failures": failures,
        "warnings": warnings,
        "evidence_sha256": evidence_sha256,
    }
    exit_code = 0 if (len(failures) == 0 and len(integrity_violations) == 0) else 2
    return (record, exit_code)


def write_computed_record(root, record):
    out_dir = _abs(root, COMPUTED_DIR_REL)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "%s_computed_gate.json" % record["prompt_id"])
    data = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return out_path


def _main(argv):
    parser = argparse.ArgumentParser(description="M6 substance verifier (M6-SGV-1.0)")
    parser.add_argument("--prompt", "--prompt-id", dest="prompt_id", default="")
    parser.add_argument("--root", default=".")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER_REL)
    parser.add_argument("--mode", choices=("gate",), default="gate")
    parser.add_argument("--write-computed", dest="write_computed", action="store_true")
    parser.add_argument("--caller", default="")
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit the JSON record on stdout for a manual run")
    args = parser.parse_args(argv)

    gate_caller = str(args.caller or "").strip().lower() == "gate"
    if gate_caller:
        # Silence all stderr chatter under --caller gate so gate mode writes
        # ONLY the single stdout JSON object and nothing to stderr on success.
        global _SUPPRESS_INFO
        _SUPPRESS_INFO = True

    if not args.prompt_id:
        parser.error("--prompt is required")

    record, exit_code = verify_prompt(args.root, args.ledger, args.prompt_id.strip(), args.mode)

    if args.write_computed:
        try:
            out_path = write_computed_record(args.root, record)
            _info("computed record written: %s" % out_path)
        except OSError as exc:
            _info("warning: could not write computed record: %r" % exc)

    if gate_caller or args.as_json:
        # Machine output: the single JSON object on stdout (the gate parses it).
        print(json.dumps(record, sort_keys=True))
    else:
        # Human output: "name: PASS/FAIL (...)" mirroring the M6 validators.
        if exit_code == 0:
            print("m6_substance_verifier: PASS (%s %s)" % (args.prompt_id.strip(),
                                                           record["computed_status"]))
        else:
            problems = list(record["failures"]) + list(record["integrity_violations"])
            print("m6_substance_verifier: FAIL (%d) for %s"
                  % (len(problems), args.prompt_id.strip()))
            for p in problems[:40]:
                print("  - " + p)
    return exit_code


def main(argv=None):
    try:
        return _main(argv if argv is not None else sys.argv[1:])
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - gate treats exit 3 as fail-closed
        prompt_id = ""
        argv_list = argv if argv is not None else sys.argv[1:]
        for i, token in enumerate(argv_list):
            if token in ("--prompt", "--prompt-id") and i + 1 < len(argv_list):
                prompt_id = argv_list[i + 1]
        minimal = {
            "prompt_id": prompt_id,
            "checked_at": _now_iso(),
            "rules_version": RULES_VERSION,
            "computed_status": "FAIL",
            "integrity_violations": [],
            "failures": ["internal verifier error (fail closed): %r" % exc],
            "warnings": [],
        }
        print(json.dumps(minimal, sort_keys=True))
        return 3


if __name__ == "__main__":
    sys.exit(main())
