from __future__ import annotations

import os
import subprocess


def resolve_secret(*, env_name: str, keychain_service: str | None = None,
                   keychain_account: str | None = None) -> str:
    value = os.environ.get(env_name)
    if not value and keychain_service:
        command = ["security", "find-generic-password", "-s", keychain_service]
        if keychain_account:
            command.extend(["-a", keychain_account])
        command.append("-w")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            value = result.stdout.strip()
    if not value:
        raise ValueError(f"{env_name} is not set and no configured Keychain password was found")
    return value
