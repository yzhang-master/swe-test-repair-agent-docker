import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from swe_repair.docker_runner import CommandEvidence, DockerRunner
from swe_repair.patch import (
    PatchProposal,
    SourceLocation,
    SourceProbe,
    apply_exact_patch,
    traceback_locations,
)
from swe_repair.workspace import IsolatedWorkspace


@dataclass(frozen=True)
class Bug:
    id: str
    root: Path

    @property
    def repo(self) -> Path:
        return self.root / "repo"

    @property
    def script(self) -> dict:
        return json.loads((self.root / "script.json").read_text(encoding="utf-8"))


@dataclass
class CandidateResult:
    proposal: PatchProposal
    diff: str
    validation: CommandEvidence


@dataclass
class RepairReport:
    bug_id: str
    resolved: bool
    baseline: CommandEvidence
    probe: SourceProbe | None = None
    localization: CommandEvidence | None = None
    traceback_locations: list[SourceLocation] = field(default_factory=list)
    candidates: list[CandidateResult] = field(default_factory=list)
    stop_reason: str = ""
    workspace_cleaned: bool = False

    def to_dict(self):
        return asdict(self)


class PatchProposer(Protocol):
    def localize(self, bug: Bug, baseline: CommandEvidence) -> SourceProbe: ...

    def propose(
        self,
        bug: Bug,
        localization: SourceProbe,
        previous: list[CandidateResult],
    ) -> PatchProposal: ...


class ScriptedPatchProposer:
    def localize(self, bug: Bug, baseline: CommandEvidence) -> SourceProbe:
        del baseline
        return SourceProbe(**bug.script["localization"])

    def propose(
        self,
        bug: Bug,
        localization: SourceProbe,
        previous: list[CandidateResult],
    ) -> PatchProposal:
        del localization
        proposals = bug.script["patches"]
        if len(previous) >= len(proposals):
            raise IndexError(f"script for {bug.id} has no more patches")
        return PatchProposal(**proposals[len(previous)])


class RepairAgent:
    def __init__(
        self,
        runner: DockerRunner,
        proposer: PatchProposer,
        max_candidates: int = 3,
    ):
        self.runner = runner
        self.proposer = proposer
        self.max_candidates = max_candidates

    def repair(self, bug: Bug) -> RepairReport:
        with IsolatedWorkspace(bug.repo) as workspace:
            baseline = self.runner.run_pytest(workspace.repo)
            report = RepairReport(bug.id, resolved=False, baseline=baseline)
            try:
                if baseline.passed:
                    report.stop_reason = "baseline tests unexpectedly passed"
                    return report
                report.traceback_locations = traceback_locations(baseline.stdout + baseline.stderr)
                report.probe = self.proposer.localize(bug, baseline)
                report.localization = self.runner.run_probe(workspace.repo, report.probe.probe)
                if report.localization.passed:
                    report.stop_reason = "localization probe did not reproduce the fault"
                    return report
                for _ in range(self.max_candidates):
                    proposal = self.proposer.propose(bug, report.probe, report.candidates)
                    candidate_repo = workspace.candidate(len(report.candidates) + 1)
                    diff = apply_exact_patch(candidate_repo, proposal)
                    validation = self.runner.run_pytest(candidate_repo)
                    report.candidates.append(CandidateResult(proposal, diff, validation))
                    if validation.passed:
                        report.resolved = True
                        report.stop_reason = "candidate passed the complete pytest suite"
                        return report
                report.stop_reason = "candidate budget exhausted"
                return report
            finally:
                report.workspace_cleaned = True
