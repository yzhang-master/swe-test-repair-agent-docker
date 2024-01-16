from pathlib import Path
from tempfile import TemporaryDirectory

from swe_repair import IsolatedWorkspace

with TemporaryDirectory() as directory:
    source = Path(directory)
    (source / "example.py").write_text("answer = 42\n")
    with IsolatedWorkspace(source) as workspace:
        assert (workspace.repo / "example.py").read_text() == "answer = 42\n"
print("isolated workspace smoke passed")
