"""Fail-closed helpers for the zero-cost Kaggle and Cloudflare demonstration."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

QUICK_TUNNEL_HOST = re.compile(r"^[a-z0-9-]+\.trycloudflare\.com$")


def validate_demo_token(environment: dict[str, str]) -> None:
    """Reject missing or weak API credentials without returning their value."""
    if len(environment.get("TRIAGE_API_TOKEN", "")) < 32:
        raise ValueError("TRIAGE_API_TOKEN must contain at least 32 characters")


def cloudflared_command(binary: Path, *, port: int = 8000) -> list[str]:
    """Build the development-only Quick Tunnel command for a loopback API."""
    if not 1 <= port <= 65535:
        raise ValueError("API port must be between 1 and 65535")
    return [
        str(Path(binary)),
        "tunnel",
        "--no-autoupdate",
        "--url",
        f"http://127.0.0.1:{port}",
    ]


def extract_quick_tunnel_url(log_text: str) -> str | None:
    """Return only a credential-free HTTPS TryCloudflare origin from logs."""
    candidates = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", log_text.lower())
    if not candidates:
        return None
    url = candidates[-1]
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not QUICK_TUNNEL_HOST.fullmatch(parsed.hostname)
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Unexpected Quick Tunnel URL")
    return f"https://{parsed.hostname}"
