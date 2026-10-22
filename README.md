# Mechanical Keyboard Audio Simulator

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Windows desktop app that plays mechanical keyboard sound effects when you type. Choose a soundpack, adjust its volume, and keep the listener running in the system tray.

## Features

- Listens for keyboard events across the desktop using `pynput` without suppressing normal key input.
- Plays a sound on the initial key press and ignores repeated press events while a key remains held.
- Selects from soundpacks discovered in the `sounds/` folder.
- Provides a volume control, live keystroke display, and a keystroke counter.
- Supports system tray controls for showing the window, toggling the listener, and exiting.
- Uses character-specific recordings when available, along with configured scan-code sounds, special-key sounds, and fallback samples.

> **Privacy:** The app observes keyboard events to trigger sounds. It does not suppress or record key input, but it needs keyboard-listening access from the operating system. Pause the listener in the app when you do not want it active.

## Requirements

- Windows 10 or later
- Python 3.10 or later
- An audio output device

## Getting started

### Run with the included launcher

Double-click `run.bat`. It uses the project's `.venv` if one exists; otherwise it runs `python main.py` from your PATH.

### Set up from a terminal

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks virtual environment activation, run the interpreter directly instead:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Using the app

1. Start the app. The keyboard listener starts automatically.
2. Choose a brand and soundpack from the dropdowns.
3. Set the volume with the slider.
4. Use **Stop Keyboard Listener** to pause sound playback while continuing to use the keyboard normally.
5. Minimize the window to the system tray. Right-click the tray icon to reopen the window, toggle the listener, or exit.

Closing the window minimizes it to the tray. Choose **Exit** from the tray menu to stop the listener and close the app.

## Soundpacks

Soundpacks are loaded from `sounds/` and are not installed through `requirements.txt`. The app scans one brand directory and one model directory deep:

```text
sounds/
└── Brand Name/
    └── Model Name/
        ├── default.wav
        ├── space.wav
        └── ...
```

Supported audio formats are `.wav`, `.mp3`, and `.ogg`. A model folder needs at least one supported audio file to appear in the selectors. The app can use files named for individual characters, common special keys (such as `space`, `enter`, `backspace`, and `shift`), or a `config.json` containing Mechvibes-style scan-code mappings. If no matching key sound exists, it falls back to an available default or sample sound.

The repository includes several soundpacks. Their source and license information may differ from the application's MIT license; check any `LICENSE` files included with individual packs before redistributing those audio files.

## Project files

| File or directory | Purpose |
| --- | --- |
| `main.py` | Application window, soundpack loading, audio playback, and keyboard listener |
| `sounds/` | Bundled soundpacks |
| `requirements.txt` | Python package dependencies |
| `run.bat` | Windows launcher |
| `LICENSE` | MIT license for the project code |

## Troubleshooting

- **No soundpacks appear:** Check that audio files are inside `sounds/<brand>/<model>/` and use WAV, MP3, or OGG format.
- **No audio plays:** Check the selected Windows output device and the app's volume setting. Some audio files or devices may not work with every backend.
- **The app cannot listen for keys:** Check whether your security or accessibility settings are blocking global keyboard hooks.
- **The window seems to have closed:** The close button minimizes the app to the system tray. Use the tray menu to show it again or exit.

## License

The application code is distributed under the [MIT License](LICENSE). Bundled sound files may have separate terms; consult the license information in each soundpack directory.
