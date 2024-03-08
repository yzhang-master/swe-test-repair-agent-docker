import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from swe_repair.agent import RepairAgent, ScriptedPatchProposer
from swe_repair.catalog import load_catalog
from swe_repair.docker_runner import DockerRunner


def run_benchmark(catalog: Path) -> dict:
    runner = DockerRunner(timeout_seconds=90)
    runner.ensure_image()
    agent = RepairAgent(runner, ScriptedPatchProposer())
    started = time.perf_counter()
    reports = [agent.repair(bug) for bug in load_catalog(catalog)]
    resolved = sum(report.resolved for report in reports)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "docker_version": subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        "image": runner.image,
        "bug_count": len(reports),
        "resolved": resolved,
        "resolve_rate": resolved / len(reports),
        "candidate_validations": sum(len(report.candidates) for report in reports),
        "docker_runs": sum(2 + len(report.candidates) for report in reports),
        "elapsed_seconds": time.perf_counter() - started,
        "all_workspaces_cleaned": all(report.workspace_cleaned for report in reports),
        "bugs": [report.to_dict() for report in reports],
    }
