# Installation

## Requirements

- Python 3.13 or newer
- Tkinter support in your Python install
- A desktop environment capable of opening Tk windows

On some Linux distributions, Tk is packaged separately from Python. If `tkinter` is missing, install the OS package that provides it and try again.

## Install from PyPI

## Recommended: `pipx`

```bash
pipx install urllib_gui
```

## Alternative: `pip`

```bash
pip install urllib_gui
```

## From source

```bash
git clone https://github.com/matthewdeanmartin/urllib_gui.git
cd urllib_gui
uv sync --all-extras
```

## Launching

Show CLI help:

```bash
urllib_gui --help
```

Launch the GUI:

```bash
urllib_gui
```

Open a URL immediately:

```bash
urllib_gui https://example.com
```

Start in dark mode:

```bash
urllib_gui --theme dark https://example.com
```

You can also run it as a module:

```bash
python -m urllib_gui https://example.com
```
