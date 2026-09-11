"""OD-011 sign-off (d) / M6.md:401 Security-Privacy — IMPORT-SCAN GATE.

The runtime app must import NO external HTTP / network-egress client. External send stays outbox+worker-only
with EXTERNAL_SEND = Final "OFF" (test_no_direct_external_send.py covers the behavioural no-send invariant);
THIS gate is the static complement — it fails the build the moment any module under app/ imports an HTTP
client, BEFORE the M6-OD-011 runtime bind adds FastAPI / uvicorn / psycopg. Today it passes only because
nothing imports such a client; this test keeps it that way once real dependencies are opened.

Detection is by AST (reads the source text), so a banned import is caught even if the library is not installed
in the venv. Scope is app/ only — test helpers may import an HTTP client for mocking without tripping the gate.
"""
from __future__ import annotations

import ast
from pathlib import Path

import app

# Top-level egress clients an M6 measurement runtime must never import.
_BANNED_TOP = frozenset({"httpx", "requests", "aiohttp", "urllib3"})
# Dotted modules where only the network-egress submodule is banned (urllib.parse / http.status stay allowed).
_BANNED_DOTTED = frozenset({"urllib.request", "http.client"})

_APP_DIR = Path(app.__file__).resolve().parent


def _banned(name: "str | None") -> "str | None":
    if not name:
        return None
    if name.split(".")[0] in _BANNED_TOP:
        return name.split(".")[0]
    for dotted in _BANNED_DOTTED:
        if name == dotted or name.startswith(dotted + "."):
            return dotted
    return None


def _scan_source(source: str, label: str) -> "list[tuple[str, int]]":
    hits: "list[tuple[str, int]]" = []
    for node in ast.walk(ast.parse(source, filename=label)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _banned(alias.name)
                if hit:
                    hits.append((hit, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            hit = _banned(node.module)
            if hit:
                hits.append((hit, node.lineno))
            # `from urllib import request` / `from http import client`
            if node.module in ("urllib", "http"):
                for alias in node.names:
                    hit2 = _banned(f"{node.module}.{alias.name}")
                    if hit2:
                        hits.append((hit2, node.lineno))
    return hits


def test_app_imports_no_http_client():
    """AST-scan every app/**.py; fail listing any module that imports httpx / requests / aiohttp / urllib3 /
    urllib.request / http.client. Keeps external egress outbox-worker-only (RULE-004) after the OD-011 bind."""
    offenders: "list[str]" = []
    for py in sorted(_APP_DIR.rglob("*.py")):
        for mod, lineno in _scan_source(py.read_text(encoding="utf-8"), str(py)):
            offenders.append(f"{py.relative_to(_APP_DIR.parent).as_posix()}:{lineno} imports '{mod}'")
    assert not offenders, "app/ must import no HTTP/network-egress client:\n  " + "\n  ".join(offenders)


def test_import_scan_detects_a_planted_violation():
    """The gate is non-vacuous: the scanner flags each banned form (proves the test above can go red)."""
    for src in ("import httpx", "import requests as r", "from aiohttp import ClientSession",
                "import urllib.request", "from urllib import request", "from http import client",
                "import urllib3"):
        assert _scan_source(src, "<probe>"), f"scanner missed a banned import: {src!r}"
    # allowed neighbours must NOT trip it
    for src in ("import urllib.parse", "from http import HTTPStatus", "import json", "from app import config"):
        assert not _scan_source(src, "<probe>"), f"scanner false-positive on: {src!r}"
