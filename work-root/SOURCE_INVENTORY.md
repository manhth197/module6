# SOURCE_INVENTORY — source integrity comparison

**Prompt**: M6-P0008 (SOURCE_INVENTORY) · Role: PM_ORCHESTRATOR · Mode: analysis_only
**Recorded**: 2026-07-20 · Executor did NOT open the archived .docx (hard rule #7).
The .docx hash was produced by the OPERATOR via Get-FileHash and pasted into the session.

## Source document

| Field | Value |
|---|---|
| Document | MODULE_6_ADS_MEASUREMENT_ROAS_V0.3_CLEAN_FINAL.docx |
| Owner doc id | GFD-M6-ADS-ROAS-TECHDESC-003 |
| Version | V0.3 Clean Final |
| Archive location | `D:\M6\source-archive\MODULE_6_ADS_MEASUREMENT_ROAS_V0.3_CLEAN_FINAL.docx` (OUTSIDE the pack) |

## SHA256 comparison

| Source | SHA256 | Size (bytes) |
|---|---|---|
| Manifest (`00-spec/registers/SOURCE_MANIFEST.md`) | `c2b03a3e34c5a519eb8b52a201390ff398ee1f653c5b2a07702547d19350fc26` | 483,752 |
| Operator `Get-FileHash` of the archived .docx | `c2b03a3e34c5a519eb8b52a201390ff398ee1f653c5b2a07702547d19350fc26` | 483,752 |

- **HASH_MATCH = True** (case-insensitive hex compare)
- **SIZE_MATCH = True**

The archived source .docx on disk is byte-for-byte the same document the pack was
extracted from — no drift or corruption since extraction (2026-07-02).

## Extract + appendix presence

- Canonical extract `00-spec/M6_FULL_DETAIL_EXTRACT.md` — **exists**.
- Its **appendix** — **exists** as the in-file section
  "EXTRACTION NOTES (appendix added by the build pack, NOT owner content)" at
  line 516 of the extract (there is no separate `*APPENDIX*` file; the appendix
  is a section within the extract, confirmed by grep).
- Companion `00-spec/M6_FULL_DETAIL_EXTRACT.rawdump.txt` — also present.

Manifest-recorded provenance (not re-run here): extraction tool
`scripts/docx_extract.py`; coverage `scripts/extract_verify.py` 707/707 blocks
FAITHFUL; 8/8 adversarial section verifications FAITHFUL, hidden-content sweep
clean.

## Verdict

- Acceptance check "manifest sha256 equals operator-supplied hash": **satisfied** (MATCH).
- Acceptance check "extract present": **satisfied** (extract + appendix + rawdump present).

Final PASS/FAIL is the runner gate + Judge's call.

## Method (read-only, no .docx opened)

Read `SOURCE_MANIFEST.md` for the recorded hash; confirmed extract/appendix via
Glob + grep; compared the manifest hash against the operator-pasted `Get-FileHash`
value with a pure string comparison (no `.docx` access). No state touched.
