import json
from pathlib import Path

from swe_repair.catalog import load_catalog

BUGS = Path(__file__).parents[1] / "data" / "bugs"


def test_catalog_contains_four_independent_executable_bug_specs():
    bugs = load_catalog(BUGS)
    assert [bug.id for bug in bugs] == [
        "chunk-boundary",
        "even-median",
        "stable-deduplication",
        "whitespace-normalization",
    ]
    for bug in bugs:
        script = json.loads(json.dumps(bug.script))
        assert script["localization"]["path"] == script["patches"][0]["path"]
        assert (bug.repo / "tests").is_dir()
        assert script["patches"]
