# swe-test-repair-agent-docker

> **Era:** 2023–2024 · Senior AI Engineer focus area (repository repair agents). Technique from 2023, reimplemented in 2026.

Isolated-workspace test reproduction and Docker-based patch validation. The repair loop,
curated bugs, benchmark, and measured results are implemented in subsequent commits.

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
python scripts/smoke.py
```

## License

MIT
