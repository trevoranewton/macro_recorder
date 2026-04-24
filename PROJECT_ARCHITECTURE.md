# Macro Recorder Project Architecture

## Overview
This project is a Python-based macro recording and playback system designed to capture real user input and replay it with high fidelity. It records mouse and keyboard activity in real time, stores events as structured JSON, and replays them with preserved timing.

The system is built as a modular automation framework with clear separation between recording, execution, and orchestration.

## Core Architecture
The system is divided into three independent scripts that communicate through a shared `control.txt` file:

- `macro_controller.py` - orchestrates the system
- `record_macro.py` - captures input events
- `execute_macro.py` - replays recorded actions

Each component runs in its own subprocess to prevent conflicts between input listeners and input simulation.

## Version Control
The project is tracked with Git, providing:

- Full history of changes and experiments
- Ability to revert to stable versions
- Incremental tracking of feature development
- Safer refactoring and architectural evolution

## `macro_controller.py` (Pipeline Manager)
The controller is the central command layer of the system.

### Responsibilities
- Launches and terminates recording and playback subprocesses
- Switches between recording and execution modes
- Handles global hotkeys:
- `Ctrl + Shift + 1` -> recording mode
- `Ctrl + Shift + 2` -> playback mode
- `Ctrl + Shift + 0` -> start/stop execution
- Writes commands to `control.txt` for inter-process communication

### Behavior
- Ensures only one mode (record or playback) runs at a time
- Terminates the opposing process when switching modes
- Uses subprocesses to isolate execution environments

## `record_macro.py` (Input Capture Engine)
This script captures all user input in real time and converts it into structured event data.

### Features
- Captures:
- Mouse movement (`x`, `y`) with `pynput`
- Mouse clicks (button and press/release state)
- Keyboard key down and key up events with the `keyboard` library
- Records precise timing between events using relative delays
- Displays a countdown popup before recording begins (`tkinter`)
- Uses `control.txt` to toggle recording state

### Data Handling
- Events are stored as JSON objects
- Timing is recorded as delay between events (not absolute timestamps)
- Recording state is reset for each new session

### Input Filtering
- Removes the `Ctrl + Shift + 0` control hotkey sequence from recorded events to prevent contamination of macro data
- No additional noise filtering (for example mouse smoothing or deduplication) is currently applied

### Output Structure
Macros are stored in a structured directory format:

```text
Macros/
  macro_name/
    macro_name_raw.json
```

Users are prompted to name and save recordings after completion.

## `execute_macro.py` (Playback Engine)
This script replays recorded macros using system-level input simulation.

### Features
- Lists available macro folders and supports chain selection with CLI input
- Loads multiple macro JSON files and builds a playback plan
- Supports finite chain runs (N cycles) or indefinite playback
- Replays events sequentially while preserving recorded delays
- Simulates mouse and keyboard input using `pynput`
- Uses modular playback classes for easier extension

### Execution Logic
Playback is driven by a loop-based chain player:

- Continuously checks elapsed time against each event's delay
- Executes each event once delay thresholds are met
- Advances through events and clips with index-based state
- Increments chain-run counters when a full sequence completes
- Stops automatically when target run count is reached (or continues indefinitely)

This approach avoids per-event sleep calls and maintains smoother playback timing.

### Input Simulation
- Mouse control via `pynput.mouse.Controller`
- Keyboard control via `pynput.keyboard.Controller`

### Platform Behavior
- Uses `msvcrt` to clear input buffer, making parts of execution Windows-specific

## Control System
All scripts communicate using a shared file:

`control.txt`

### Commands
- `record_start`
- `record_stop`
- `play_start`
- `play_stop`

### Behavior
- Scripts continuously poll the file for commands
- Commands are executed immediately when detected
- The file is cleared after reading to prevent duplicate execution

## Key Design Decisions
### Subprocess Isolation
Separating components prevents:

- Input listener conflicts
- Blocking execution
- Cross-interference between recording and playback

### File-Based Communication
Using a shared text file instead of sockets or queues:

- Simplifies debugging
- Removes external dependencies
- Keeps the system lightweight and local

### Event-Based Recording Model
Capturing discrete events with timing:

- Enables deterministic replay
- Minimizes storage complexity
- Allows future transformation or editing of macros

### Loop-Based Execution Engine
Using a continuous loop with time checks instead of fixed delays:

- Improves playback consistency
- Reduces timing drift
- Allows smoother execution of recorded input

## Limitations
- Dependent on static screen positions (no UI awareness)
- No GUI for macro editing or management
- No conditional logic or branching in execution
- No dynamic resolution or scaling handling
- Limited input filtering (only control hotkey removal)

## Future Improvements
- GUI-based macro manager and editor
- Playback speed control
- Conditional logic and branching
- Per-clip repeat counts inside a single chain plan
- Smarter input filtering (movement thresholds, deduplication)
- Resolution-independent execution
- Integration with external triggers or APIs

## Summary
This project implements a full input automation pipeline:

`Capture -> Store -> Execute -> Control`

It provides a modular, process-isolated system with accurate timing control, reliable execution, and a scalable foundation for future automation features.
