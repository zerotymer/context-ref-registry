"""Regression test for the multi-worker JWT secret infinite-login-loop bug.

uvicorn `--workers N` spawns N independent processes that each import
`app.config` on their own. The JWT signing secret was generated per process
(`secrets.token_hex(32)` at import time), so a token signed by worker A failed
signature validation in worker B with a 401. Under round-robin load balancing
this made the same request alternate 200/401, and the frontend looped forever
on re-login.

The fix sources the secret from the JWT_SECRET environment variable (exported
once by entrypoint.sh) so every worker shares one value. These tests reproduce
two workers as two subprocesses and assert cross-worker token validity.
"""
import os
import subprocess
import sys
import uuid
from pathlib import Path

# backend/ root — so the subprocess can `import app...`.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_SAMPLE_UUID = uuid.UUID(int=0x1234)


def _run_worker(snippet: str, *, jwt_secret: str | None) -> str:
    """Run a Python snippet in a fresh process, mimicking one uvicorn worker."""
    env = dict(os.environ)
    if jwt_secret is None:
        env.pop("JWT_SECRET", None)
    else:
        env["JWT_SECRET"] = jwt_secret
    proc = subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(_BACKEND_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_workers_with_shared_env_secret_agree() -> None:
    secret = "a1b2c3d4" * 8  # 64 hex chars, like token_hex(32)
    read_secret = "import app.config as c; print(c.JWT_SECRET)"
    worker_a = _run_worker(read_secret, jwt_secret=secret)
    worker_b = _run_worker(read_secret, jwt_secret=secret)
    assert worker_a == worker_b == secret


def test_token_signed_by_one_worker_validates_in_another() -> None:
    secret = "f0f0f0f0" * 8
    sign = (
        "import uuid; from app.service.auth_service import create_access_token; "
        f"print(create_access_token(uuid.UUID(int={_SAMPLE_UUID.int})))"
    )
    token = _run_worker(sign, jwt_secret=secret)

    decode = (
        "from app.service.auth_service import decode_access_token; "
        f"print(decode_access_token({token!r}))"
    )
    decoded = _run_worker(decode, jwt_secret=secret)
    assert decoded == str(_SAMPLE_UUID)


def test_token_is_rejected_when_secrets_differ() -> None:
    # The original bug: two workers with different secrets. The signing worker's
    # token must be rejected by a worker holding a different secret (401), which
    # is exactly what the env-shared secret prevents in production.
    sign = (
        "import uuid; from app.service.auth_service import create_access_token; "
        f"print(create_access_token(uuid.UUID(int={_SAMPLE_UUID.int})))"
    )
    token = _run_worker(sign, jwt_secret="1111111111" * 6 + "1111")

    decode = (
        "from app.exceptions import RegistryError; "
        "from app.service.auth_service import decode_access_token; "
        f"\ntry:\n    decode_access_token({token!r}); print('ACCEPTED')\n"
        "except RegistryError as e:\n    print(f'REJECTED:{e.status_code}')"
    )
    result = _run_worker(decode, jwt_secret="2222222222" * 6 + "2222")
    assert result == "REJECTED:401"
