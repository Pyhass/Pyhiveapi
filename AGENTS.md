# Repository Guidelines

## Project Structure & Module Organization
Primary source lives in `src/`. `src/hive.py` exposes the public `Hive` entry point, built on `HiveSession` in `src/session.py`. Network and auth code sits in `src/api/`; shared constants, helpers, and dataclasses are in `src/helper/`; sample JSON payloads used for file-backed flows are in `src/data/`.

This package is authored as async-first code. `src/__init__.py` switches between async and sync API/auth implementations, and `setup.py build_py` generates the sync package from the async source. Make changes in `src/` only.

Tests live in `tests/`. The current suite is small, with focused checks like `tests/test_hub.py` and support code in `tests/common.py`.

## Build, Test, and Development Commands
Install dependencies:

```bash
pip install -r requirements.txt -r requirements_test.txt
```

Run tests with `pytest tests/`.
Run one test with `pytest tests/test_hub.py::test_force_update_polls_when_idle`.
Run lint and local checks with `pre-commit run --all-files`.
Generate the sync build with `python setup.py build_py`.

Useful targeted checks:
`black src/`, `isort src/`, `flake8 src/`, `pylint src/`, `bandit --configfile=tests/bandit.yaml src/`.

## Coding Style & Naming Conventions
Use 4-space indentation and modern Python compatible with `python_requires >=3.10`. Keep formatting Black-compatible; `isort` is configured with the Black profile in `setup.cfg`. Prefer `snake_case` for new functions and methods, and `PascalCase` for classes and dataclasses.

Preserve backward-compatible aliases only when public API stability requires them. Avoid editing generated artifacts or adding new logic outside the async source tree.

## Testing Guidelines
Use `pytest` and `pytest-asyncio` for async behavior. Name files `test_*.py` and test functions `test_*`. Favor narrow tests around session polling, auth flow edges, and device state mapping. There is no stated coverage threshold in the repo, so contributors should add tests for each behavioral change rather than relying on broad suite coverage.

## Commit & Pull Request Guidelines
Recent history uses concise imperative commit subjects, for example `Fix test_hub.py...` and `Refactor device data handling...`. Keep commits scoped to one change.

Open PRs with a clear summary, linked issue when relevant, and the exact checks you ran. The repository’s workflow docs show a branch-based release flow through `dev` and `master`, so avoid assuming direct pushes to release branches are acceptable.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
