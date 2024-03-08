# swe-test-repair-agent-docker

> **Era:** 2023–2024 · Senior AI Engineer focus area (repository repair agents). Technique from 2023, reimplemented in 2026.

A deterministic test-repair workflow that reproduces failing pytest suites in isolated copies, confirms a source fault with an executable probe, applies exact source patches, and runs every applied candidate in real Docker. It reports only a four-bug local curated set—there are no claimed SWE-bench results.

## Problem

A patch is not a repair merely because a model produced a plausible diff. Reliable evaluation needs a genuinely failing baseline, evidence tying the failure to source behavior, independent candidate validation, and cleanup that cannot silently modify the original repository.

## Method

```text
curated source ──copy──> temporary baseline ──Docker pytest──> failing evidence
                                  │
                                  ├─Docker executable probe──> confirmed fault
                                  │
                                  ├─fresh copy + exact patch 1──Docker pytest──> pass/fail
                                  └─fresh copy + exact patch N──Docker pytest──> pass/fail
                                                               │
                                                               └─delete workspace/container
```

`IsolatedWorkspace` copies the source into a temporary directory. The original tree is never a Docker mount or patch target. `traceback_locations` extracts non-test source frames when pytest emits them, while the proposer's targeted Python probe supplies a second, executable fault signal; a passing probe stops repair.

Each `PatchProposal` is an exact, unique, non-empty source replacement. Patches cannot modify tests, escape the workspace, or apply ambiguously. Every candidate starts from the pristine baseline. A bug is resolved only after its baseline fails, its probe fails, and one candidate's **complete** pytest suite exits zero.

`DockerRunner` invokes the Docker CLI directly. Containers have no network, no Linux capabilities, `no-new-privileges`, a bounded temporary filesystem, and a bind-mounted candidate workspace. They use `--rm`; timed-out workloads are force-removed. The `swe-repair-pytest:3.12` image is built from `python:3.12-slim` with pytest 9.2.0.

`ScriptedPatchProposer` reads a bug-specific localization probe and ordered patches. It makes the complete workflow deterministic and requires neither an LLM nor API keys. The median bug deliberately proposes a wrong lower-middle patch first, so candidate rejection is part of the measured run.

## Results

Measured locally on 2026-11-14 with Docker server 29.1.3, Python 3.12 in the container, and pytest 9.2.0. Full commands, exit codes, stdout/stderr, timings, diffs, and container names are in the generated `results/benchmark.json`.

| Curated bug | Baseline | Candidate Docker pytest runs | Resolved |
|---|---|---:|---|
| Chunk iteration skips items | 1 failed, 2 passed | 1 | yes |
| Even median returns upper middle value | 1 failed, 2 passed | 2 (wrong, then correct) | yes |
| Deduplication loses first-occurrence order | 1 failed, 1 passed | 1 | yes |
| Whitespace normalization only trims spaces | 1 failed, 2 passed | 1 | yes |
| **Total** | **4 failing baselines** | **5** | **4/4 (100%)** |

The run executed **13 Docker workloads** in **15.114 seconds**: four baseline pytest runs, four failing localization probes, and five full candidate pytest runs. All temporary workspaces were cleaned. The integration test additionally checks that every container is absent and hashes the curated source before and after repair to confirm it is unchanged.

This 100% resolve rate describes only four known bugs with scripted known-good patches. It is not an SWE-bench score or evidence of autonomous general-purpose repair.

## Reproduce

Docker must be installed and its daemon available. No Python packages are installed into the host repository or shared environments.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
python scripts/smoke.py
python scripts/benchmark.py
```

`pytest` includes a real Docker integration test when the Docker CLI is present. The first run builds the local test image; later runs reuse it. `scripts/smoke.py` repairs the chunk-boundary bug end to end. The benchmark writes its detailed evidence report to `results/benchmark.json` (ignored by Git).

To inspect retained evidence without rerunning all tests:

```bash
python -m json.tool results/benchmark.json
```

## Limitations

- Four small, curated Python bugs with predetermined patches measure workflow correctness, not model-driven localization accuracy or unseen-repository generalization.
- Exact string replacement is intentionally auditable but cannot express multi-file or ambiguous edits. There is no live LLM patch proposer in this repository.
- Passing the supplied tests can still miss incorrect behavior; test quality bounds repair quality. Wrong patches are rejected only when the suite detects them.
- Docker isolation limits the workload's network and capabilities, but the writable bind mount and local Docker trust model are not a security boundary for hostile code. Use a stronger sandbox for untrusted repositories.
- The image is pulled/built from external base and package sources on first use. Tests skip the Docker integration case only when the CLI is absent; daemon or image-build failures otherwise fail explicitly.

## References

- S. Yao et al. *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR 2023. arXiv:2210.03629
- C. E. Jimenez et al. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024. arXiv:2310.06770
- [Docker run security options](https://docs.docker.com/engine/reference/run/#security-configuration)
- [pytest usage and exit codes](https://docs.pytest.org/en/stable/reference/exit-codes.html)

## License

MIT
