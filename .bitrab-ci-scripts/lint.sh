#!/usr/bin/env bash
set -euo pipefail
source ./.bitrab-ci-scripts/setup.sh
uv run isort --check-only urllib_gui tests
uv run black --check urllib_gui tests
uv run ruff check --quiet urllib_gui tests
uv run pylint --score=n --reports=n --rcfile=.pylintrc urllib_gui
uv run pylint --score=n --reports=n --rcfile=.pylintrc_tests tests
