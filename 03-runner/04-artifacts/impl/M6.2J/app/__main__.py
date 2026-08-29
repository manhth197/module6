"""`python -m app` entrypoint (satisfies the LOCKED run_command).

Prints the staged posture and exits 0. Starts no server, opens no socket, calls nothing external.
"""
from __future__ import annotations

from app import config


def main() -> int:
    print("Module 6 - slice M6.2A measurement foundation (STAGED)")
    print(
        f"global_gateway_state={config.GLOBAL_GATEWAY_STATE} "
        f"production_flag={config.PRODUCTION_FLAG} "
        f"external_send={config.EXTERNAL_SEND}"
    )
    print("measure-only; no external send; no scale; no publish; no flag flips.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
