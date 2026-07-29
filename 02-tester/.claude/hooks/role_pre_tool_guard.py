#!/usr/bin/env python3
# role_pre_tool_guard.py -- PreToolUse hook (M6 build pack), Python fallback.
# Byte-identical copy shipped to every role folder; canonical master lives in
# setup/hooks-master/. Behavior must stay identical to role_pre_tool_guard.ps1.
#
# Blocks (exit 2 + reason on stderr):
#   (a) danger patterns anywhere in the raw payload: production-flag flips,
#       gateway-state flips, secret assignments, live token shapes;
#   (b) mutating shell verbs combined with denied roots -- scanned ONLY in
#       command/script fields, never in Write/Edit file content;
#   (c) Write/Edit/MultiEdit paths outside the role allowlist or inside
#       deny roots (absolute paths inside the role project are normalized
#       to relative first; absolute paths outside the project are blocked).
# Fail-closed: unparseable payload or missing policy file => block.
import sys, os, json, re

def block(reason):
    sys.stderr.write("ROLE_PRE_TOOL_GUARD BLOCK: " + reason + "\n")
    sys.exit(2)

def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        block("empty hook payload (fail-closed)")
    try:
        payload = json.loads(raw)
    except Exception:
        block("unparseable hook payload (fail-closed)")

    hook_dir = os.path.dirname(os.path.abspath(__file__))
    role_root = os.path.dirname(os.path.dirname(hook_dir))
    policy_path = os.path.join(role_root, ".claude", "role_policy.json")
    if not os.path.isfile(policy_path):
        block("role_policy.json missing (fail-closed)")
    try:
        with open(policy_path, encoding="utf-8") as f:
            policy = json.load(f)
    except Exception:
        block("role_policy.json unparseable (fail-closed)")

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}

    # ------------- (a) danger patterns on the whole payload -------------
    danger = [
        ("production flag flip", r'(?i)production_flag\s*"?\s*[:=]\s*"?\s*(ON|TRUE|1|ENABLED)\b'),
        ("gateway state flip",   r'(?i)global_gateway_state\s*"?\s*[:=]\s*"?\s*(OPEN|READY|PASS|UNLOCKED|GO)\b'),
        ("meta token shape",     r'EAA[A-Za-z0-9]{20,}'),
        ("openai token shape",   r'sk-[A-Za-z0-9_\-]{20,}'),
        ("github token shape",   r'gh[pousr]_[A-Za-z0-9]{20,}'),
        ("slack token shape",    r'xox[baprs]-[A-Za-z0-9\-]{10,}'),
        ("aws key shape",        r'AKIA[0-9A-Z]{16}'),
        ("google key shape",     r'AIza[0-9A-Za-z_\-]{30,}'),
        ("jwt shape",            r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}'),
    ]
    for name, rx in danger:
        if re.search(rx, raw):
            block("danger pattern detected: " + name)
    secret_rx = (r'(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|'
                 r'access[_-]?key|verify[_-]?token|private[_-]?key)\b'
                 r'\s*[:=]\s*[\'"]([^\'"\r\n]{12,})[\'"]')
    for m in re.finditer(secret_rx, raw):
        val = m.group(2)
        if not re.match(r'^(secret_ref|vault:|\$\{|\{\{|<|MASKED|REDACTED|PLACEHOLDER|EXAMPLE)', val):
            block("secret assignment with literal value (use secret_ref)")

    # ------------- (b) shell verb + denied root, command fields only ----
    deny_roots = [str(r) for r in (policy.get("deny_write_roots") or [])]
    cmd_text = ""
    for f in ("command", "script"):
        if isinstance(tool_input, dict) and tool_input.get(f):
            cmd_text += " " + str(tool_input[f])
    if cmd_text.strip():
        # Redirection alt uses (?<![-=]) so display arrows -> and => do NOT trip
        # it, while real redirection > and >> still match (false-positive fix).
        verb_rx = (r'(?i)(\brm\b|\bdel\b|\berase\b|\brmdir\b|\brd\b|Remove-Item|\bri\b|'
                   r'\bmv\b|\bmove\b|Move-Item|\bren\b|Rename-Item|Set-Content|Add-Content|'
                   r'Out-File|Clear-Content|New-Item|\bcp\b|\bcopy\b|Copy-Item|\btee\b|(?<![-=])>{1,2})')
        has_verb = re.search(verb_rx, cmd_text) is not None
        norm_cmd = cmd_text.replace("\\", "/")
        for root in deny_roots:
            needle = root.replace("\\", "/").rstrip("/")
            if not needle:
                continue
            if re.search(re.escape(needle), norm_cmd) and has_verb:
                block("mutating shell verb touching denied root: " + root)

    # ------------- (c) Write/Edit path allowlist ------------------------
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        file_path = ""
        if isinstance(tool_input, dict):
            file_path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        if not file_path.strip():
            block("write tool without file path (fail-closed)")
        norm = file_path.replace("/", "\\")
        root_norm = role_root.rstrip("\\")
        if re.match(r"^[A-Za-z]:\\", norm) or norm.startswith("\\\\"):
            full = os.path.abspath(norm)
            if not full.lower().startswith(root_norm.lower() + "\\"):
                block("absolute write path outside role project: " + file_path)
            norm = full[len(root_norm) + 1:]
        if ".." in norm:
            block("path traversal in write path")
        rel = norm.replace("\\", "/").lstrip("/")
        for root in deny_roots:
            needle = root.replace("\\", "/").rstrip("/")
            if not needle:
                continue
            if rel == needle or rel.lower().startswith(needle.lower() + "/"):
                block("write into denied root: " + root)
        allow_roots = [str(r) for r in (policy.get("allowed_write_roots") or [])]
        allowed = False
        for root in allow_roots:
            needle = root.replace("\\", "/").rstrip("/")
            if not needle:
                continue
            if rel == needle or rel.lower().startswith(needle.lower() + "/"):
                allowed = True
                break
        if not allowed:
            block("write path not in role allowlist: " + rel)

    sys.exit(0)

if __name__ == "__main__":
    main()
