import shutil
import tempfile
from pathlib import Path


class IsolatedWorkspace:
    def __init__(self, source: Path, parent: Path | None = None):
        self.source = source.resolve()
        self._temporary = tempfile.TemporaryDirectory(prefix="swe-repair-", dir=parent)
        self.root = Path(self._temporary.name)
        self.repo = self.root / "baseline"
        shutil.copytree(self.source, self.repo)

    def candidate(self, index: int) -> Path:
        destination = self.root / f"candidate-{index}"
        shutil.copytree(self.repo, destination)
        return destination

    def cleanup(self):
        self._temporary.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cleanup()
