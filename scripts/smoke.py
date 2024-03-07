from pathlib import Path

from swe_repair import DockerRunner, RepairAgent, ScriptedPatchProposer
from swe_repair.catalog import load_catalog

root = Path(__file__).resolve().parents[1]
bug = load_catalog(root / "data" / "bugs")[0]
report = RepairAgent(DockerRunner(), ScriptedPatchProposer()).repair(bug)
assert report.resolved, report.stop_reason
assert report.workspace_cleaned
print(f"{bug.id}: resolved; Docker pytest exit={report.candidates[-1].validation.returncode}")
