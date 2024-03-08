import hashlib
from pathlib import Path

from swe_repair import RepairAgent, ScriptedPatchProposer
from swe_repair.catalog import load_catalog
from swe_repair.docker_runner import CommandEvidence

BUGS = Path(__file__).parents[1] / "data" / "bugs"


def evidence(returncode):
    return CommandEvidence(["fake"], returncode, "metrics.py, line 8", "", 0.0, "fake")


class FakeRunner:
    def __init__(self, baseline_returncode=1, probe_returncode=1):
        self.baseline_returncode = baseline_returncode
        self.probe_returncode = probe_returncode
        self.pytest_calls = 0

    def run_pytest(self, repo: Path):
        self.pytest_calls += 1
        if self.pytest_calls == 1:
            return evidence(self.baseline_returncode)
        source = repo / "metrics.py"
        passed = source.exists() and "+ ordered[middle]) / 2" in source.read_text()
        return evidence(0 if passed else 1)

    def run_probe(self, repo: Path, probe: str):
        return evidence(self.probe_returncode)


def fingerprint(path: Path):
    return {
        str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob("*")
        if item.is_file()
    }


def test_wrong_candidate_fails_then_correct_candidate_resolves_without_source_changes():
    bug = load_catalog(BUGS)[1]
    assert bug.id == "even-median"
    before = fingerprint(bug.repo)
    runner = FakeRunner()
    report = RepairAgent(runner, ScriptedPatchProposer()).repair(bug)
    assert report.resolved
    assert len(report.candidates) == 2
    assert report.candidates[0].validation.returncode == 1
    assert report.candidates[1].validation.passed
    assert report.localization.returncode == 1
    assert report.workspace_cleaned
    assert fingerprint(bug.repo) == before


def test_passing_baseline_is_not_a_repair():
    bug = load_catalog(BUGS)[1]
    report = RepairAgent(FakeRunner(baseline_returncode=0), ScriptedPatchProposer()).repair(bug)
    assert not report.resolved
    assert report.stop_reason == "baseline tests unexpectedly passed"
    assert not report.candidates


def test_unconfirmed_localization_stops_before_patching():
    bug = load_catalog(BUGS)[1]
    report = RepairAgent(FakeRunner(probe_returncode=0), ScriptedPatchProposer()).repair(bug)
    assert not report.resolved
    assert report.stop_reason == "localization probe did not reproduce the fault"
    assert not report.candidates
