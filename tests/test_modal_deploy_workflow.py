from pathlib import Path


def test_modal_deployment_requires_an_explicit_manual_confirmation():
    workflow = Path(".github/workflows/deploy-modal.yml").read_text()

    assert "workflow_dispatch:" in workflow
    assert "confirm_deploy:" in workflow
    assert "if: ${{ inputs.confirm_deploy }}" in workflow
    assert "environment: modal-demo" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "modal deploy -m deploy.modal_app" in workflow
    assert "evaluate_triage_endpoint.py" in workflow
    assert "if: ${{ false }}" not in workflow
    assert "push:" not in workflow
