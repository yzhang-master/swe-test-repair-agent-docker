import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from swe_repair import DockerRunner, RepairAgent, ScriptedPatchProposer
from swe_repair.catalog import load_catalog

BUGS = Path(__file__).parents[1] / "data" / "bugs"


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker CLI is required")
def test_real_docker_rejects_wrong_patch_and_accepts_fix():
    bug = next(item for item in load_catalog(BUGS) if item.id == "even-median")
    before = {
        path: hashlib.sha256(path.read_bytes()).digest()
        for path in bug.repo.rglob("*")
        if path.is_file()
    }
    report = RepairAgent(DockerRunner(timeout_seconds=90), ScriptedPatchProposer()).repair(bug)
    assert report.baseline.returncode == 1
    assert report.localization.returncode == 1
    assert [candidate.validation.returncode for candidate in report.candidates] == [1, 0]
    assert report.resolved
    assert report.workspace_cleaned
    assert before == {
        path: hashlib.sha256(path.read_bytes()).digest()
        for path in bug.repo.rglob("*")
        if path.is_file()
    }
    evidence = [report.baseline, report.localization]
    evidence.extend(candidate.validation for candidate in report.candidates)
    for run in evidence:
        assert run.command[0] == "docker"
        remaining = subprocess.run(
            ["docker", "ps", "-aq", "--filter", f"name=^{run.container_name}$"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert remaining == ""
