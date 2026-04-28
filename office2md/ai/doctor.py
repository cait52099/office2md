import shutil
import subprocess
from typing import Dict


def run_ai_checks() -> Dict[str, str]:
    checks = {
        "ai_backend": "disabled by default",
        "minimax_cli": "optional, not found",
        "mmx_cli": "optional, not found",
        "mmx_help": "not checked",
        "mmx_auth_status": "not checked",
    }

    minimax = shutil.which("minimax")
    mmx = shutil.which("mmx")
    if minimax:
        checks["minimax_cli"] = f"found: {minimax}"
    if not mmx:
        checks["mmx_auth_status"] = "optional integration not installed"
        return checks

    checks["mmx_cli"] = f"found: {mmx}"
    checks["mmx_help"] = _run_safe([mmx, "--help"])
    checks["mmx_auth_status"] = _run_safe([mmx, "auth", "status"])
    return checks


def _run_safe(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15)
    except Exception as exc:
        return f"failed: {exc.__class__.__name__}"
    if completed.returncode == 0:
        return "ok"
    stderr = (completed.stderr or "").strip().splitlines()
    stdout = (completed.stdout or "").strip().splitlines()
    message = (stderr or stdout or ["no output"])[0]
    if len(message) > 160:
        message = message[:157] + "..."
    return f"failed ({completed.returncode}): {message}"

