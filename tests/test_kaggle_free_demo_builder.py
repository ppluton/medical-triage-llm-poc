import json

from scripts.build_kaggle_free_demo import BASE_DATASET_ID, SFT_DATASET_ID, main


def test_builder_attaches_only_exact_private_model_layers(tmp_path, monkeypatch):
    metadata = {
        "id": "pierrepluton/chsa-source-sft-qwen3",
        "is_private": True,
        "machine_shape": "NvidiaTeslaT4",
        "code_file": "demo.ipynb",
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata))
    output = tmp_path / "package"
    monkeypatch.setattr(
        "sys.argv",
        ["build_kaggle_free_demo.py", "--output", str(output), "--metadata", str(metadata_path)],
    )

    main()

    built_metadata = json.loads((output / "kernel-metadata.json").read_text())
    notebook = json.loads((output / "demo.ipynb").read_text())
    serialized = json.dumps(notebook)
    assert built_metadata["dataset_sources"] == [BASE_DATASET_ID, SFT_DATASET_ID]
    assert built_metadata["kernel_sources"] == []
    assert "TRIAGE_API_TOKEN" in serialized
    assert "get_secret('TRIAGE_API_TOKEN')" in serialized
    assert "modal deploy" not in serialized
    assert "chsa-dpo" not in serialized


def test_builder_rejects_non_private_notebook(tmp_path, monkeypatch):
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "id": "pierrepluton/chsa-source-sft-qwen3",
                "is_private": False,
                "machine_shape": "NvidiaTeslaT4",
                "code_file": "demo.ipynb",
            }
        )
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "build_kaggle_free_demo.py",
            "--output",
            str(tmp_path / "package"),
            "--metadata",
            str(metadata_path),
        ],
    )

    try:
        main()
    except ValueError as error:
        assert "private T4" in str(error)
    else:
        raise AssertionError("Public notebook should be rejected")
