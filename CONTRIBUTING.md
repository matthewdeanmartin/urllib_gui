# Contributing

Thanks for working on `urllib_gui`.

This project uses `uv` for Python tooling and a Makefile for the common local commands. The CI configuration in GitHub Actions and the GitLab-style `.bitrab-ci.yml` pipeline both follow that same toolchain, so the safest local workflow is to use the same commands they use.

## Setup

```bash
git clone https://github.com/matthewdeanmartin/urllib_gui.git
cd urllib_gui
uv sync --all-extras
```

To see the available project commands:

```bash
uv run make help
```

## Common local commands

Run the full local quality gate:

```bash
uv run make check
```

Run the CI-style quality gate without formatting mutations:

```bash
uv run make check-ci
```

Run individual checks:

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

The main GitHub Actions build installs dependencies with:

```bash
uv sync --all-extras
```

Then it runs:

```bash
uv run make check-ci
```

There is also a separate `tox` workflow that runs `tox -e py` on:

- Ubuntu and Windows
- Python 3.13 and 3.14

## GitLab-style / Bitrab pipeline

The repository also includes `.bitrab-ci.yml`, which splits work into separate jobs:

- `lint`: isort, black, ruff, pylint, pylint-tests
- `mypy`: mypy strict on `urllib_gui` and `tests`
- `precommit`: `uv run pre-commit run --all-files`
- `pytest`: pytest with coverage, JUnit, and xdist
- `smoke`: `uv run bash scripts/basic_checks.sh`
- `bandit`: Bandit against `urllib_gui`
- `audit`: `uv audit` and `pip-audit`
- `check_docs`: interrogate, codespell, and spelling-focused pylint
- `build_docs`: `uv run mkdocs build`
- `build_package`: `uv build`

All of those jobs bootstrap with `uv sync --all-extras`.

## Expectations for changes

- Use `uv`, not bare `pip` or `pytest`.
- Keep tests in `tests/`.
- Update docs and the README when behavior or workflow changes.
- Prefer the existing Make targets instead of ad hoc command lines when a target already exists.

For code changes, run at least the relevant targeted checks and, before opening a PR, run:

```bash
uv run make check
```

If you want to mirror the main GitHub Actions gate exactly, also run:

```bash
uv run make check-ci
```

## Docs work

Documentation is built with MkDocs:

```bash
uv run make build-docs
```

The Read the Docs build uses `mkdocs.yml`, so documentation changes should leave the docs with a real home page and a clean MkDocs build.
