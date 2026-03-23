# ⌨️ typer

A terminal typing speed test. No browser, no distractions.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- ⌨️ **Three difficulty modes** — Easy, Medium (tech words), Hard (long words)
- 📊 **Live WPM counter** as you type
- ✅ **Accuracy tracking** — per character precision
- 🏆 **Personal best leaderboard** — top 20 scores saved locally
- 🎨 **Color coded feedback** — green for correct, red for mistakes

## Install

```bash
git clone https://github.com/30Sana/typer.git
cd typer
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Select difficulty with `1`, `2`, or `3`. Space to submit each word. `Ctrl+C` to quit.

## Requirements

- Python 3.8+
- `rich`
- macOS / Linux (uses `tty` for raw input)

## License

MIT