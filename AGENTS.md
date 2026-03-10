# AGENTS.md

## Architecture map (quick orientation)
- `pygase/connection.py`: protocol and transport core. Defines package/header serialization, sequence/ack tracking, connection status, and client/server connection classes that send and receive UDP datagrams.
- `pygase/backend.py`: server-side orchestration layer. Wraps lower-level connection behavior with backend lifecycle management, event dispatch wiring, and game loop integration.
- `pygase/client.py`: client-facing API. Manages connecting/disconnecting to a backend, event exchange, and synchronized state consumption for game/application code.
- `pygase/gamestate.py`: authoritative state model and update mechanics. Defines game state containers, ordered updates, and merge/apply behavior used by both client and backend flows.

## Canonical `uv` commands
- Setup (dev env + editable install):
  - `uv sync`
- Format:
  - `uv run black pygase tests`
- Type-check:
  - `uv run mypy pygase`
- Lint/docstyle:
  - `uv run pylint --fail-under=9.9 pygase`
  - `uv run pydocstyle pygase`
- Targeted tests (single file or subset):
  - `uv run pytest -m "not integration" tests/connection_test.py`
  - `uv run pytest -m "not integration" tests -k connection`
- Quick default test pass (fast feedback):
  - `uv run pytest -m "not integration" tests`
- Integration tests only:
  - `uv run pytest -m integration tests`
- Full tests (match CI intent):
  - `uv run pytest tests --doctest-modules --cov=pygase --cov-report=term-missing`

## Fast path vs full validation
- Fast path (small, local edits that do not affect protocol, networking, or cross-module behavior):
  1. `uv run black pygase tests`
  2. `uv run pytest -m "not integration" tests/<affected_module>_test.py`
  3. `uv run mypy pygase` (required before finishing any task)
- Full validation (required for protocol/network behavior edits, connection timing/ordering changes, or broad refactors):
  1. `uv run black pygase tests`
  2. `uv run pytest tests --doctest-modules --cov=pygase --cov-report=term-missing`
  3. `uv run mypy pygase`
  4. `uv run pylint --fail-under=9.9 pygase`
  5. `uv run pydocstyle pygase`

## Testing conventions
- Test modules follow `tests/*_test.py` naming (e.g., `connection_test.py`, `backend_test.py`).
- Add new tests to the most specific existing module first; create a new `*_test.py` only when introducing a clearly new surface area.
- Keep unit tests close to behavior boundaries:
  - protocol/package encoding/decoding in `connection_test.py`
  - backend lifecycle/event handling in `backend_test.py`
  - client integration points in `client_test.py`
  - state/update semantics in `gamestate_test.py`
- Use integration tests (`tests/integration_test.py`) when validating real interactions across client/backend/connection boundaries, especially message ordering, retries, ack behavior, and state sync flows that cannot be trusted from isolated mocks.
- Tests marked with `@pytest.mark.integration` are socket/network or timing-sensitive; exclude them by default with `-m "not integration"` for fast local iteration.

## Troubleshooting common failures
- UDP/socket flakiness:
  - Re-run failing tests first to check for non-determinism.
  - Avoid asserting exact timing for network delivery; prefer eventual assertions and bounded waits.
  - Ensure sockets/async tasks are properly closed to prevent port reuse issues across tests.
- Timing assumptions:
  - Tests that depend on scheduler timing should use robust margins and avoid brittle sleep-based exactness.
  - If a failure appears time-sensitive, inspect event loop load and replace strict sequence-on-time assertions with sequence/eventual-state assertions where appropriate.

## Documentation source-of-truth vs generated output
- Editable documentation sources live in repository root files such as `README.md`, `getting-started.md`, and documentation build configuration (`pydocmd.yml`).
- The `docs/` tree is generated site output (`site_dir: docs`) and should generally not be hand-edited; regenerate it from source files/config when docs content changes.
- Search/navigation tooling may ignore generated `docs/` artifacts (for example via `.rgignore`) to reduce noise, but this does not change packaging/build behavior.

## Completion gate for coding agents
- Before marking work as done, always run static type checking: `uv run mypy pygase`.
- Before marking work as done, always run docstring style checks: `uv run pydocstyle pygase`.
- Treat mypy failures as blocking; fix findings or explicitly document environment limitations if they prevent execution.
- Treat pydocstyle failures as blocking; fix findings or explicitly document environment limitations if they prevent execution.

