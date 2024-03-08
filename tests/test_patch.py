from pathlib import Path

import pytest

from swe_repair.patch import PatchError, PatchProposal, apply_exact_patch, traceback_locations


def proposal(old="value = 1\n", new="value = 2\n", path="module.py"):
    return PatchProposal(path=path, old=old, new=new, rationale="test")


def test_exact_patch_changes_only_source_and_returns_diff(tmp_path: Path):
    (tmp_path / "module.py").write_text("value = 1\n")
    diff = apply_exact_patch(tmp_path, proposal())
    assert (tmp_path / "module.py").read_text() == "value = 2\n"
    assert "-value = 1" in diff
    assert "+value = 2" in diff


@pytest.mark.parametrize(
    "change",
    [
        proposal(old="missing"),
        proposal(old="value = 1\n", new="value = 1\n"),
        proposal(path="tests/test_module.py"),
        proposal(path="../outside.py"),
    ],
)
def test_invalid_patches_are_rejected(tmp_path: Path, change: PatchProposal):
    (tmp_path / "module.py").write_text("value = 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_module.py").write_text("value = 1\n")
    with pytest.raises(PatchError):
        apply_exact_patch(tmp_path, change)


def test_ambiguous_patch_is_rejected(tmp_path: Path):
    (tmp_path / "module.py").write_text("value = 1\nvalue = 1\n")
    with pytest.raises(PatchError, match="exactly one"):
        apply_exact_patch(tmp_path, proposal())


def test_traceback_localization_excludes_tests_and_dependencies():
    output = """
Traceback:
  File "/workspace/tests/test_metrics.py", line 8, in test
  File "/workspace/metrics.py", line 8, in median
  File "/usr/local/lib/python3.12/site-packages/pytest.py", line 2, in run
"""
    locations = traceback_locations(output)
    assert [(item.path, item.line) for item in locations] == [("metrics.py", 8)]
