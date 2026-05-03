# Contributing

Thanks for contributing to `urllib_gui`.

This project uses `uv` for Python tooling and keeps most common workflows behind Make targets. The existing CI setup follows that pattern too, so the easiest way to stay aligned with CI is to use the same commands locally.

## Setup

```bash
git clone https://github.com/matthewdeanmartin/urllib_gui.git
cd urllib_gui
uv sync --all-extras
```

List the available project commands:

```bash
uv run make help
```

## Local quality gates

Run the full local quality gate:

```bash
uv run make check
```

Run the CI-style quality gate:

```bash
uv run make check-ci
```

Run targeted commands:

```bash
uv run make lint
uv run make typecheck
uv run make test
uv run make security
uv run make docs-check
uv run make build-docs
uv run make smoke
uv run make tox
```

Useful supporting commands:

```bash
uv run make format
uv run make format-check
uv run make spell
uv run make prerelease
```

## What CI runs

## GitHub Actions

The main GitHub Actions workflow installs dependencies with:

```bash
uv sync --all-extras
```

Then it runs:

```bash
uv run make check-ci
```

The separate `tox` workflow runs `tox -e py` on Ubuntu and Windows for Python 3.13 and 3.14.

## GitLab-style / Bitrab pipeline

The repository also ships a GitLab-style pipeline in `.bitrab-ci.yml`. It splits work into separate jobs for:

- lint
- mypy
- precommit
- pytest
- smoke
- bandit
- audit
- check_docs
- build_docs
- build_package

Those jobs all bootstrap with:

```bash
uv sync --all-extras
```

And their underlying scripts run the same tools you would expect from the Makefile:

- isort, black, ruff, pylint, pylint-tests
- mypy strict
- pre-commit
- pytest with coverage and JUnit output
- the CLI smoke script
- Bandit, `uv audit`, and `pip-audit`
- MkDocs docs build
- `uv build`

## Before opening a PR

- run `uv run make check`
- update tests when behavior changes
- update the docs and README when the user-facing workflow changes
- use the existing Make targets instead of inventing new local commands when a target already exists

For docs-only changes, at minimum make sure:

```bash
uv run make build-docs
```
