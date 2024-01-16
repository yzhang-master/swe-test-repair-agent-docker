from pathlib import Path

from swe_repair import IsolatedWorkspace


def test_workspace_copies_and_cleans_source(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    original = source / "module.py"
    original.write_text("value = 1\n")
    with IsolatedWorkspace(source) as workspace:
        root = workspace.root
        copied = workspace.repo / "module.py"
        copied.write_text("value = 2\n")
        assert original.read_text() == "value = 1\n"
    assert not root.exists()
