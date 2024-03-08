import argparse
import json
from pathlib import Path

from swe_repair.benchmark import run_benchmark

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Repair every curated bug with real Docker validation")
parser.add_argument("--catalog", type=Path, default=ROOT / "data" / "bugs")
parser.add_argument("--output", type=Path, default=ROOT / "results" / "benchmark.json")
args = parser.parse_args()
report = run_benchmark(args.catalog)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
