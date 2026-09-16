from __future__ import annotations

import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_cloudflare_pages_build_contains_static_demo_without_secrets(tmp_path):
    output = tmp_path / "pages"
    subprocess.run(
        [
            "python3",
            str(REPOSITORY_ROOT / "scripts" / "build_cloudflare_pages.py"),
            "--output",
            str(output),
        ],
        check=True,
    )

    assert {"index.html", "styles.css", "app.js", "_headers", "_routes.json"} <= {
        path.name for path in output.iterdir()
    }
    assert (output / "docs" / "index.html").is_file()
    page = (output / "index.html").read_text()
    script = (output / "app.js").read_text()
    routes = (output / "_routes.json").read_text()
    assert 'href="styles.css"' in page and 'src="app.js"' in page
    assert 'fetch("/v1/triage"' in script
    assert '"include": ["/v1/triage"]' in routes
    combined = "\n".join(path.read_text() for path in output.rglob("*") if path.is_file())
    assert "MODAL_API_TOKEN" not in combined
    assert "DEMO_ACCESS_TOKEN" not in combined


def test_cloudflare_proxy_is_fail_closed_and_streams_modal_response():
    source = (
        REPOSITORY_ROOT
        / "deploy"
        / "cloudflare_pages"
        / "functions"
        / "v1"
        / "triage.js"
    ).read_text()
    assert 'target.protocol !== "https:"' in source
    assert '.endsWith(".modal.run")' in source
    assert "crypto.subtle.timingSafeEqual" in source
    assert 'return jsonResponse(401, "Unauthorized")' in source
    assert 'return jsonResponse(503, "Demonstration backend is not configured")' in source
    assert "readBoundedBody(request)" in source
    assert "total > MAX_BODY_BYTES" in source
    assert "body," in source
    assert "new Response(upstream.body" in source
    assert "console.log" not in source


def test_cloudflare_deploy_workflow_is_manual_and_gated():
    workflow = (
        REPOSITORY_ROOT / ".github" / "workflows" / "deploy-cloudflare-pages.yml"
    ).read_text()
    assert "workflow_dispatch:" in workflow
    assert "confirm_deploy:" in workflow
    assert "if: ${{ inputs.confirm_deploy }}" in workflow
    assert "environment: cloudflare-demo" in workflow
    assert "CLOUDFLARE_API_TOKEN" in workflow
    assert "--project-name=chsa-triage-poc" in workflow
    assert "push:" not in workflow
