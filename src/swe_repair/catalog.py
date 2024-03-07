from pathlib import Path

from swe_repair.agent import Bug


def load_catalog(root: Path) -> list[Bug]:
    return [Bug(path.name, path) for path in sorted(root.iterdir()) if path.is_dir()]
