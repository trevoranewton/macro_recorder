# Macro App Worklog

This document tracks project decisions and implementation progress as an ongoing engineering log.

## 2026-04-24 - Project Documentation Foundation

### Goals
- Establish durable project documentation.
- Separate high-level onboarding from technical architecture details.

### Decisions
- `README.md` should remain concise and onboarding-focused.
- Architecture-level details should live in `PROJECT_ARCHITECTURE.md`.
- Runtime/user data should not be committed to source control.

### Completed
- Converted architecture content from Word source into `PROJECT_ARCHITECTURE.md`.
- Updated `README.md` structure and aligned script names with actual files.
- Removed obsolete Word-based architecture file after conversion.

---

## 2026-04-24 - Branching + Git Workflow

### Goals
- Isolate collaboration work from `main`.
- Ensure every completed task is documented via commits.

### Decisions
- Active collaboration branch: `codex-collab-2026-04-24`.
- Use focused commits with clear intent and validation notes.
- Prefer frequent pushes after verified milestones.

### Completed
- Created and pushed collaboration branch.
- Established commit-first workflow for feature and bug history.

---

## 2026-04-24 - Playback System Modularization

### Goals
- Support chaining macros and controlled repetition.
- Move from single-loop macro playback toward configurable sequence execution.

### Decisions
- Introduce modular playback internals in `execute_macro.py`.
- Preserve event timing fidelity while expanding sequence logic.

### Completed
- Refactored playback code into modular, state-driven flow.
- Added sequence execution support with loop controls.
- Updated docs to reflect new architecture and behavior.

---

## 2026-04-24 - Sequence UX Specification (Clarification Pass)

### Goals
- Lock down exact behavior before additional code churn.
- Optimize for streamlined terminal interaction.

### Key Product Decisions
- Per-step repeat defaults to `1` unless overridden.
- Per-step repeat can be `N` or `inf`.
- `inf` allowed only on final sequence step.
- Save/load reusable sequence presets.
- Presets may include repeated macro references in different steps.
- Loaded presets should run as-saved (no edit pass on load).
- Sequence loop count is set at playback time (not stored in preset by default).
- Playback stop behavior:
- `play_stop` pauses immediately.
- `play_start` resumes at current step but restarts that step from repeat `1`.
- Missing macro reference in preset should raise explicit error:
- `"macro_name" macro does not exist`.

### Completed
- Implemented agreed sequence model and prompt flow in `execute_macro.py`.
- Added preset persistence via `sequence_presets.json`.

---

## 2026-04-24 - Playback Menu + Hotkey Evolution

### Goals
- Keep quick single-macro runs available.
- Separate playback consumption from sequence creation.

### Decisions
- Add dedicated configure hotkey:
- `Ctrl + Shift + 1` -> Record Mode
- `Ctrl + Shift + 2` -> Playback Mode
- `Ctrl + Shift + 3` -> Configure Sequence Mode
- `Ctrl + Shift + 0` -> Start/Stop toggle for active mode
- Playback mode menu should be simplified to:
- `1. Load saved sequence`
- `2. Load macro`
- Sequence creation should happen in Configure Sequence Mode only.

### Completed
- Implemented new hotkey mapping and process startup modes.
- Split execute startup behavior into playback vs configure flows.
- Updated `README.md` and `PROJECT_ARCHITECTURE.md`.

---

## 2026-04-24 - Reliability and UX Bug Fixes

### Goals
- Eliminate friction during mode transitions and replay toggling.

### Completed
- Fixed replay toggle after auto-complete:
- `Ctrl + Shift + 0` now restarts playback correctly after sequence completion.
- Fixed configure -> playback handoff:
- playback now restarts execute process when startup mode changes.
- Fixed intermittent `^@` input artifact:
- replaced prompt reads with hardened `msvcrt` line reader that ignores control-byte noise from hotkeys.
- Simplified configure prompt interaction:
- changed from typed `done` to empty Enter to finish input.
- new prompt text:
- `Select macro number or press Enter when done:`

---

## 2026-04-24 - Recording Improvement for Sequence Chaining

### Goals
- Improve cross-macro chaining reliability by anchoring cursor state.

### Completed
- Recording now injects an initial mouse `move` event at start using current cursor position.
- Delay baseline is initialized immediately after seed event for correct timing.

---

## Source Control Guardrails

### Decisions
- Macro data and preset runtime data should remain local, not committed.

### Completed
- Updated `.gitignore` to ignore:
- `macros/`
- `Macros/`
- `sequence_presets.json`

---

## Current System Snapshot

### Modes
- Record Mode (`Ctrl + Shift + 1`)
- Playback Mode (`Ctrl + Shift + 2`)
- Configure Sequence Mode (`Ctrl + Shift + 3`)

### Playback Mode Options
- `1: Load saved sequence`
- `2: Load macro`

### Configure Sequence Interaction
- Display available macros.
- Add steps by number.
- Press Enter on empty input to finish (minimum 1 step).
- Step repeat input defaults to `1` when Enter is pressed.
- Step repeat accepts `N` or `inf` (`inf` restricted to last step).

### Presets
- Stored in `sequence_presets.json`.
- Contains sequence references + per-step repeat config.
- Overwrite prompt appears on naming collisions.

### Control Channel
- Uses `control.txt` commands between controller and worker scripts.
- Playback toggle command uses runtime player state to avoid stale controller state issues.

---

## Next Priority Candidates

- Add timed cycle orchestration (example: login -> action for X hours -> logout -> repeat).
- Add optional preset categorization/folder support.
- Add safe sequence editing commands (`list`, `remove`, `reorder`) in configure flow.
