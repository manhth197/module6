"""Carry-forward M6.2T -> M6.2U byte-identical (exclude caches + prior PLAN/NOTES/INVARIANTS docs)."""
import os, shutil
SRC = r"D:\M6\Module6-workspace\01-coder\04-artifacts\impl\M6.2T"
DST = r"D:\M6\Module6-workspace\01-coder\04-artifacts\impl\M6.2U"
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDE_NAMES = {"PLAN.md", "IMPLEMENTATION_NOTES.md"}
EXCLUDE_SUFFIX = (".pyc", ".pyo")
def ignore(dirpath, names):
    ig = set()
    for n in names:
        full = os.path.join(dirpath, n)
        if os.path.isdir(full) and n in EXCLUDE_DIRS: ig.add(n)
        elif n in EXCLUDE_NAMES: ig.add(n)
        elif n.endswith(EXCLUDE_SUFFIX): ig.add(n)
        elif n.upper().startswith("INVARIANT"): ig.add(n)
    return ig
shutil.copytree(SRC, DST, dirs_exist_ok=True, ignore=ignore)
def count(root, ext=None):
    c = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        for f in fns:
            if ext is None or f.endswith(ext): c += 1
    return c
print("carried OK  M6.2U total:", count(DST), " .py:", count(DST, ".py"), " .sql:", count(DST, ".sql"), " PLAN:", os.path.exists(os.path.join(DST,"PLAN.md")))
print("M6.2T .py:", count(SRC, ".py"), " .sql:", count(SRC, ".sql"))
