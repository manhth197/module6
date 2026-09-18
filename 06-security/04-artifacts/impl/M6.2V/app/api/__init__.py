"""M6 HTTP-facing handlers (M6.2B). Framework-neutral: pure request handlers, no server/routing here.

The concrete HTTP framework, routing, and status-code mapping are an owner-controlled integration step bound to
M6-OD-011 (stack.framework is unset). These handlers are that binding's testable core; they perform NO external
send (RULE-004) and flip no flag (staged BLOCKED/OFF).
"""
