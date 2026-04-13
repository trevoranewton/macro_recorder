# Macro Recorder (Python)

A custom-built macro recording and playback system written in Python.

## Features

* Record mouse and keyboard input with precise timing
* Save macros as JSON files
* Replay macros with accurate timing and looping behavior
* Hotkey-based control system (start/stop recording and playback)
* Modular architecture with separate controller, recorder, and executor

## Tech Stack

* Python
* pynput (input tracking)
* JSON (data storage)
* subprocess (process control)

## How It Works

* `Macro Controller.py` manages mode switching (record vs playback)
* `Record Macro.py` captures user input and saves it
* `Execute Macro.py` replays recorded actions with timing control

## Use Case

Built as a foundation for automation workflows and game interaction scripting.

## Future Improvements

* GUI interface
* Macro editing tools
* Smarter playback logic
