# Macro Recorder (Python)

A Python macro recording and playback system that captures real mouse and keyboard input, stores events as JSON, and replays them with preserved timing.

## Features
- Record mouse and keyboard input with precise timing
- Save macros as JSON files
- Automatically captures the current mouse position at recording start
- Playback menu options: load saved sequence or load single macro
- Build sequences with per-step repeat counts (`1`, `N`, or `inf`)
- Repeat the full sequence (`1`, `N`, or `inf`) at playback time
- Save and load reusable sequence presets
- Replay macros with accurate timing behavior
- Hotkey-based control system (start/stop recording and playback)
- Modular architecture with separate controller, recorder, and executor

## Project Structure
- `macro_controller.py` manages mode switching (record vs playback)
- `record_macro.py` captures user input and saves macro event files
- `execute_macro.py` builds playback chains and executes timed replay
- `control.txt` is used for inter-process command signaling
- `Macros/` stores recorded macro data
- `sequence_presets.json` stores saved sequence presets (macro references + repeat config)

## Hotkeys
- `Ctrl + Shift + 1` -> Record Mode
- `Ctrl + Shift + 2` -> Playback Mode
- `Ctrl + Shift + 3` -> Configure Sequence Mode
- `Ctrl + Shift + 0` -> Start/Stop (toggle for current mode)

## Documentation
- Architecture and design details: `PROJECT_ARCHITECTURE.md`

## Tech Stack
- Python
- `pynput` (input tracking and simulation)
- `keyboard` (keyboard event capture)
- JSON (data storage)
- `subprocess` (process control)

## Status
This project is an active foundation for automation workflows and game interaction scripting.
