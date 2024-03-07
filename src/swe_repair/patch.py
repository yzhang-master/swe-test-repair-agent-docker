import difflib
import re
from dataclasses import dataclass
from pathlib import Path


class PatchError(ValueError):
    pass


@dataclass(frozen=True)
class SourceProbe:
    path: str
    line: int
    probe: str
    rationale: str


@dataclass(frozen=True)
class PatchProposal:
    path: str
    old: str
    new: str
    rationale: str


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int


def traceback_locations(output: str) -> list[SourceLocation]:
    locations = []
    for path, line in re.findall(r'File "(?:/workspace/)?([^"\n]+)", line (\d+)', output):
        relative = Path(path)
        if (
            "site-packages" not in relative.parts
            and "tests" not in relative.parts
            and not relative.name.startswith("test_")
        ):
            location = SourceLocation(str(relative), int(line))
            if location not in locations:
                locations.append(location)
    return locations


def apply_exact_patch(repo: Path, proposal: PatchProposal) -> str:
    target = (repo / proposal.path).resolve()
    if not target.is_relative_to(repo.resolve()):
        raise PatchError("patch path escapes the repository")
    relative = target.relative_to(repo.resolve())
    if "tests" in relative.parts or relative.name.startswith("test_"):
        raise PatchError("repair candidates may not modify tests")
    if proposal.old == proposal.new:
        raise PatchError("patch must change the source")
    if not target.is_file():
        raise PatchError(f"source file does not exist: {proposal.path}")
    before = target.read_text(encoding="utf-8")
    occurrences = before.count(proposal.old)
    if occurrences != 1:
        raise PatchError(f"expected exactly one match, found {occurrences}")
    after = before.replace(proposal.old, proposal.new, 1)
    target.write_text(after, encoding="utf-8")
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{proposal.path}",
            tofile=f"b/{proposal.path}",
        )
    )
