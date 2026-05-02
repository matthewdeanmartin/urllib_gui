# Urllib Gui

<!-- TODO (generated from template — delete this block once done)
  - [ ] Replace this description with a real one-paragraph summary
  - [ ] Update pyproject.toml [project] keywords with real search terms
  - [ ] Update pyproject.toml classifiers Development Status (3-Alpha → 4-Beta → 5-Production)
  - [ ] Update pyproject.toml description (shown on PyPI)
  - [ ] Add a PyPI badge: https://badge.fury.io/py/urllib_gui
  - [ ] Add a CI badge from your GitHub Actions build.yml
  - [ ] Fill in docs/overview/README.md with a real project overview
  - [ ] Add real subcommands to urllib_gui/cli.py and update scripts/basic_checks.sh
  - [ ] Register project on Read the Docs and point it at mkdocs.yml
  - [ ] Set up PyPI OIDC trusted publishing (no token needed) for publish_to_pypi.yml
  - [ ] Run `make pre-commit-install` to install git hooks
  - [ ] Run `make gha-upgrade` after first push to pin GHA action SHAs
  - [ ] Add project-specific words to private_dictionary.txt
  - [ ] Update SECURITY.md scope section with what's actually in scope for this project
  - [ ] Update CHANGELOG.md 0.1.0 entry with real release notes
-->

A tiny urllib-shaped text browser for Tkinter. The current MVP can open HTTP/HTTPS/file URLs, render HTML into readable text, follow links in tabs, inspect source and headers, track history, save bookmarks, and copy the current request as Python `urllib` code.

## Installation

```bash
pipx install urllib_gui
```

Or with pip:

```bash
pip install urllib_gui
```

## Usage

```bash
urllib_gui --help
```

Launch the GUI directly:

```bash
python -m urllib_gui
```

Open a URL immediately:

```bash
python -m urllib_gui https://example.com
```

## Contributing

See [CONTRIBUTING.md](docs/extending/CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
