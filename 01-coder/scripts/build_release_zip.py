#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a portable Module6-workspace.zip without local venvs or junctions.

Role junctions are intentionally omitted: after extraction the operator runs
setup/Initialize-M6RoleIsolatedDesktop.ps1 to recreate them against the new
absolute pack path. Real fallback snapshots remain in the archive.
"""
import argparse
import hashlib
import os
import sys
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SKIP_DIRS = {".venv", "__pycache__", ".git"}
SKIP_FILES = {"_NEXT_PROMPT_LOCKED.md"}


def is_reparse_dir(path):
    try:
        st = os.stat(path, follow_symlinks=False)
        return bool(getattr(st, "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        kept = []
        for name in sorted(dirnames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            if name in SKIP_DIRS or is_reparse_dir(path):
                continue
            if rel == "work-root/target-repo" or rel.startswith("work-root/target-repo/"):
                continue
            kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            if name in SKIP_FILES or name.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            yield path, rel


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=os.path.join(os.path.dirname(ROOT), "Module6-workspace.zip"))
    args = parser.parse_args()
    output = os.path.abspath(args.output)
    temp = output + ".tmp"
    files = list(iter_files())
    prefix = os.path.basename(ROOT.rstrip(os.sep))
    os.makedirs(os.path.dirname(output), exist_ok=True)
    if os.path.exists(temp):
        os.remove(temp)
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, rel in files:
            z.write(path, prefix + "/" + rel)
    with zipfile.ZipFile(temp) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit("zip CRC verification failed at " + bad)
        if len([e for e in z.infolist() if not e.is_dir()]) != len(files):
            raise SystemExit("zip file count mismatch")
    os.replace(temp, output)
    print("release zip: %s" % output)
    print("files: %d" % len(files))
    print("bytes: %d" % os.path.getsize(output))
    print("sha256: %s" % sha256(output))


if __name__ == "__main__":
    main()
