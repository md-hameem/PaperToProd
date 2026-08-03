from app.pipeline.agents.scaffolder import ScaffoldOutput


def test_scaffold_output_schema():
    """Verify that the structured output schema matches expectations."""
    mock_data = {
        "file_tree": {"model.py": "Defines the model architecture"},
        "dependency_manifest": {"torch": ">=2.0.0"},
    }

    # Should not raise validation error
    output = ScaffoldOutput(**mock_data)
    assert output.file_tree["model.py"] == "Defines the model architecture"
    assert "torch" in output.dependency_manifest
