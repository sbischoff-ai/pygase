[![CI](https://github.com/sbischoff-ai/pygase/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/sbischoff-ai/pygase/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/sbischoff-ai/pygase/ci.yml?branch=master&label=tests)](https://github.com/sbischoff-ai/pygase/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/sbischoff-ai/pygase/branch/master/graph/badge.svg)](https://codecov.io/gh/sbischoff-ai/pygase)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![PyPI](https://img.shields.io/pypi/v/pygase.svg)
# PyGaSe
**Py**thon **Ga**me **Se**rver

A package for Python 3.12+ that contains a game-ready client-server architecture and UDP-based network protocol.

It deals with problems such as package loss or network congestion so you don't have to. Instead it gives you
a high-level API to easily connect clients and backends that share a synchronized game state and exchange events.
The async framework for this one is Python's built-in [asyncio](https://docs.python.org/3/library/asyncio.html).

PyGaSe is built to be easy to use, lightweight, fast, scalable and reliable.
You can build a fast-paced real-time online game with this.
You can also build a large-scale MMO with thousands of clients if you like.

I'm actively developing PyGaSe in the context of several Indie game projects and I'm happy to share it.

---
***BREAKING CHANGE**: Version 0.2.0 is basically a new API and updating from 0.1.9 or lower will break you code.*
*It is also much more stable, flexible and powerful, so make sure to use 0.2.0 or higher.*

---

### Installation
```
pip install pygase
```
or better yet `uv add pygase`.

## Usage

### API Reference & Tutorials

For API documentation and a *Getting Started* section go [here](https://sbischoff-ai.github.io/pygase/).

### Example

[This example game](https://github.com/sbischoff-ai/pygase/tree/master/chase) implements an online game of tag,
in which players can move around, while one of them is the chaser who has to catch another player.
A player who has been catched becomes the next chaser and can catch other players after a 5s protection countdown.

Run `server.py` first, then run `client.py` in additional terminal sessions to add players.
Only use the same player name once.

### Debugging & Logging

You can use the standard `logging` module. On level `INFO` you will get logging output for events such as
startups, shutdowns, new connections or disconnects. On `DEBUG` level you get detailed output right down to the level
of sending, receiving and handling single network packages.

Debug logs are also a good way to understand the inner workings of PyGaSe.

### Development

Contributors should review [`AGENTS.md`](AGENTS.md) for a quick architecture map, canonical `uv` commands,
validation scope guidance, and repository testing conventions.

Bootstrap the local development hooks once per clone:

```bash
uv run pre-commit install
```

After installing, `pre-commit` runs Black automatically on staged Python files during `git commit`.
Type checking is part of the developer validation flow. Run:

```bash
uv run mypy pygase
```

The `mypy.ini` configuration now enforces `disallow_untyped_defs` incrementally for core runtime modules (`pygase.client`, `pygase.backend`, `pygase.connection`, `pygase.event`, and `pygase.utils`) to steadily raise typing strictness without requiring an all-at-once migration.

If formatting updates are needed, the hook rewrites files and the commit stops so you can re-stage and retry.
You can also run all configured hooks manually with:

```bash
uv run pre-commit run --all-files
```

Documentation source files you should edit directly are `README.md`, `getting-started.md`, and `pydocmd.yml`.
The `docs/` directory is generated site output and should be regenerated instead of hand-edited.


### Testing

Use marker selection to keep local feedback fast while still running full pre-merge validation:

- Quick iteration (default): `uv run pytest -m "not integration" tests`
- Integration coverage only: `uv run pytest -m integration tests`
- Full pre-merge validation: `uv run pytest tests --doctest-modules --cov=pygase --cov-report=term-missing`

---
## Changes

### 0.3.1
- improved documentation
- minor logging fixes

### 0.3.0
- sticking to SemVer from here on out
- logging added using the standard `logging` module
- improve event handler arguments
- `Backend` class added to reduce server-side boilerplate
- various bugfixes

### 0.2.0
- complete overhaul of pygase 0.1.x with breaking API changes
