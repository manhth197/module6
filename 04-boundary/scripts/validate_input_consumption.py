#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_input_consumption.py -- declared inputs are actually consumed (light).

Ported from M5 (m5_validate_input_consumption_substance.py) as a light,
index-driven check. Reads 00-spec/PROMPT_INDEX_LOCKED.csv (NOT the ledger and
NOT 04-artifacts/state, which is operator-only). Never writes anything.

Rule, per index row:
  * Non-judge row -> consumption record is the row's ExpectedEvidence JSON; the
    consumed-input list is its "files_read"; the pass-signal is "status".
  * Judge row (RequiresJudge=true) -> consumption record is the row's
    ExpectedJudge sign-off JSON; the consumed-input list is its
    "evidence_reviewed"; the pass-signal is "verdict".
  When that record exists AND the pass-signal is pass-like, every RequiredInputs
  file-part (a trailing "#section" is stripped; only the file part is testable)
  must appear in the consumed-input list. Otherwise the input was declared but
  not consumed -- a substance regression.

Rows whose consumption record does not exist yet are skipped (pass): on the
pristine pre-run pack (no evidence) this is a vacuous PASS. A record that exists
but is unreadable/invalid JSON fails closed.

Prints "validate_input_consumption: PASS/FAIL (...)"; exit 0 clean / exit 2.
"""
import csv
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
INDEX = os.path.join(ROOT, "00-spec", "PROMPT_INDEX_LOCKED.csv")

PASS_LIKE = {"PASS", "SIGNED", "APPROVED", "DONE"}

problems = []


def bad(msg):
    problems.append(msg)


def norm(path):
    """Normalize a path token for membership comparison: forward slashes, no
    leading ./ or /, drop a trailing #section, case-folded (Windows paths are
    case-insensitive)."""
    s = str(path).replace("\\", "/").strip()
    s = s.split("#", 1)[0]
    while s.startswith("./"):
        s = s[2:]
    s = s.lstrip("/")
    return s.rstrip("/").lower()


def read_index():
    with open(INDEX, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_record(rel):
    """Return (exists, data). data is None when the file is absent or unreadable
    (an unreadable existing file records a problem via the caller)."""
    abs_path = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.isfile(abs_path):
        return False, None
    try:
        with open(abs_path, "rb") as f:
            return True, json.loads(f.read().decode("utf-8-sig"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return True, exc


def main():
    if not os.path.isfile(INDEX):
        print("validate_input_consumption: FAIL (1)")
        print("  - missing index: 00-spec/PROMPT_INDEX_LOCKED.csv")
        sys.exit(2)

    rows = read_index()
    enforced = 0
    skipped = 0

    for row in rows:
        pid = str(row.get("PromptId") or "").strip()
        if not pid:
            continue
        is_judge = str(row.get("RequiresJudge") or "").strip().lower() == "true"
        if is_judge:
            record_rel = str(row.get("ExpectedJudge") or "").strip()
            list_field = "evidence_reviewed"
            status_field = "verdict"
        else:
            record_rel = str(row.get("ExpectedEvidence") or "").strip()
            list_field = "files_read"
            status_field = "status"

        if not record_rel:
            # judge row without a declared sign-off path (or evidence path
            # missing): registry validator owns that shape; nothing to consume.
            skipped += 1
            continue

        exists, data = load_record(record_rel)
        if not exists:
            skipped += 1
            continue
        if isinstance(data, Exception):
            bad("%s: consumption record %s exists but is unreadable/invalid JSON (%s) (fail closed)"
                % (pid, record_rel, data))
            continue
        if not isinstance(data, dict):
            bad("%s: consumption record %s is not a JSON object (fail closed)" % (pid, record_rel))
            continue

        status_val = str(data.get(status_field) or "").strip().upper()
        if status_val not in PASS_LIKE:
            # not claiming a pass yet -> not our concern
            skipped += 1
            continue

        enforced += 1
        consumed = set()
        raw_list = data.get(list_field)
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, str):
                    consumed.add(norm(item))
        elif isinstance(raw_list, str):
            consumed.add(norm(raw_list))

        for part in str(row.get("RequiredInputs") or "").split(";"):
            part = part.strip()
            if not part:
                continue
            want = norm(part)
            if want not in consumed:
                bad("%s: RequiredInputs '%s' not in %s of %s (declared but not consumed)"
                    % (pid, part.split("#", 1)[0], list_field, record_rel))

    if problems:
        print("validate_input_consumption: FAIL (%d)" % len(problems))
        for p in problems[:60]:
            print("  - " + p)
        if len(problems) > 60:
            print("  - ... %d more" % (len(problems) - 60))
        sys.exit(2)
    print("validate_input_consumption: PASS (%d rows enforced, %d skipped-no-evidence, %d total)"
          % (enforced, skipped, len(rows)))


if __name__ == "__main__":
    main()
