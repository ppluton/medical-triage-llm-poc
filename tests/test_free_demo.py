import pytest

from triage_poc.free_demo import (
    cloudflared_command,
    extract_quick_tunnel_url,
    validate_demo_token,
)


def test_demo_token_is_required_and_not_returned():
    assert validate_demo_token({"TRIAGE_API_TOKEN": "x" * 32}) is None
    with pytest.raises(ValueError, match="at least 32"):
        validate_demo_token({"TRIAGE_API_TOKEN": "short"})


def test_cloudflared_command_exposes_only_loopback():
    command = cloudflared_command("/tmp/cloudflared", port=8123)
    assert command == [
        "/tmp/cloudflared",
        "tunnel",
        "--no-autoupdate",
        "--url",
        "http://127.0.0.1:8123",
    ]
    with pytest.raises(ValueError, match="port"):
        cloudflared_command("cloudflared", port=0)


def test_quick_tunnel_url_is_strictly_parsed():
    log = "INF Your quick Tunnel has been created! https://Calm-Tree-42.trycloudflare.com"
    assert extract_quick_tunnel_url(log) == "https://calm-tree-42.trycloudflare.com"
    assert extract_quick_tunnel_url("no endpoint yet") is None
    assert extract_quick_tunnel_url("https://trycloudflare.com.attacker.example") is None
