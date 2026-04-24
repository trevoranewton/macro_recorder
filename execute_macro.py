import json
import os
import sys
import time
import msvcrt
from dataclasses import dataclass
from typing import Dict, List, Optional

from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button, Controller as MouseController


INFINITE = None


@dataclass
class SequenceStep:
    macro_name: str
    repeats: Optional[int]  # None == infinite


@dataclass
class PlaybackPlan:
    steps: List[SequenceStep]
    sequence_loops: Optional[int]  # None == infinite


class SequencePlayer:
    def __init__(
        self,
        plan: PlaybackPlan,
        events_by_macro: Dict[str, list],
        mouse: MouseController,
        keyboard_ctrl: KeyboardController,
    ):
        self.plan = plan
        self.events_by_macro = events_by_macro
        self.mouse = mouse
        self.keyboard_ctrl = keyboard_ctrl

        self.playing = False
        self.current_step_index = 0
        self.current_step_repeat_index = 0
        self.sequence_loops_completed = 0
        self.event_index = 0
        self.last_event_time = time.time()

    def start(self) -> None:
        # Resume from current step, but restart this step from the beginning.
        self.playing = True
        self.event_index = 0
        self.current_step_repeat_index = 0
        self.last_event_time = time.time()
        print("Playback started.")

    def stop(self, reason: str = "Playback stopped.") -> None:
        if self.playing:
            print(reason)
        self.playing = False

    def step(self) -> None:
        if not self.playing or not self.plan.steps:
            return

        current_step = self.plan.steps[self.current_step_index]
        events = self.events_by_macro.get(current_step.macro_name, [])

        if not events:
            # Empty macro behaves like an instant completed run.
            self._complete_single_step_run(current_step)
            return

        if self.event_index >= len(events):
            self._complete_single_step_run(current_step)
            return

        event = events[self.event_index]
        if time.time() - self.last_event_time < event.get("delay", 0):
            return

        self.last_event_time = time.time()
        self._execute_event(event)
        self.event_index += 1

    def _complete_single_step_run(self, current_step: SequenceStep) -> None:
        self.event_index = 0
        self.last_event_time = time.time()

        if current_step.repeats is INFINITE:
            return

        self.current_step_repeat_index += 1
        if self.current_step_repeat_index < current_step.repeats:
            return

        self.current_step_repeat_index = 0
        self.current_step_index += 1

        if self.current_step_index < len(self.plan.steps):
            return

        self.current_step_index = 0
        self.sequence_loops_completed += 1

        if (
            self.plan.sequence_loops is not INFINITE
            and self.sequence_loops_completed >= self.plan.sequence_loops
        ):
            self.current_step_index = 0
            self.current_step_repeat_index = 0
            self.event_index = 0
            self.stop("Playback complete: sequence loop target reached.")

    def _execute_event(self, event: dict) -> None:
        event_type = event.get("type")

        if event_type == "move":
            self.mouse.position = (event["x"], event["y"])
            return

        if event_type == "click":
            button = Button.left if "left" in event.get("button", "") else Button.right
            if event.get("pressed"):
                self.mouse.press(button)
            else:
                self.mouse.release(button)
            return

        if event_type == "key":
            key = parse_key(event.get("key", ""))
            action = event.get("action")
            if action == "down":
                self.keyboard_ctrl.press(key)
            elif action == "up":
                self.keyboard_ctrl.release(key)
            return

        # "noop" or unknown event types are ignored.


def clear_input_buffer() -> None:
    while msvcrt.kbhit():
        msvcrt.getch()


def read_user_input(prompt_text: str) -> str:
    # Use manual console reading so control chars from hotkeys
    # (like Ctrl+2 -> NUL) are ignored instead of being echoed as "^@".
    print(prompt_text, end="", flush=True)
    chars: List[str] = []

    while True:
        ch = msvcrt.getwch()

        # Handle Enter
        if ch in ("\r", "\n"):
            print("")
            return "".join(chars).strip()

        # Handle Ctrl+C
        if ch == "\x03":
            raise KeyboardInterrupt

        # Ignore Windows extended/special key markers.
        if ch in ("\x00", "\xe0"):
            # Extended keys are often 2-part sequences.
            if msvcrt.kbhit():
                _ = msvcrt.getwch()
            continue

        # Handle backspace editing.
        if ch == "\b":
            if chars:
                chars.pop()
                print("\b \b", end="", flush=True)
            continue

        # Ignore other non-printable control chars.
        if ord(ch) < 32:
            continue

        chars.append(ch)
        print(ch, end="", flush=True)


def parse_key(key_str: str):
    try:
        return getattr(Key, key_str)
    except AttributeError:
        return key_str


def parse_positive_int(value: str) -> Optional[int]:
    try:
        parsed = int(value)
        if parsed >= 1:
            return parsed
    except ValueError:
        pass
    return None


def prompt_repeats(prompt_text: str) -> Optional[int]:
    while True:
        raw = read_user_input(prompt_text).lower()
        if raw == "":
            return 1
        if raw in {"inf", "infinite", "indefinite"}:
            return INFINITE
        parsed = parse_positive_int(raw)
        if parsed is not None:
            return parsed
        print("Enter a whole number >= 1, or 'inf'.")


def prompt_menu_choice(max_value: int, prompt_text: str) -> int:
    while True:
        raw = read_user_input(prompt_text)
        parsed = parse_positive_int(raw)
        if parsed is not None and parsed <= max_value:
            return parsed
        print(f"Enter a number between 1 and {max_value}.")


def read_json_file(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def write_json_file(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_available_macros(macro_dir: str) -> List[str]:
    return sorted(
        [name for name in os.listdir(macro_dir) if os.path.isdir(os.path.join(macro_dir, name))]
    )


def load_macro_events(macro_dir: str, macro_name: str) -> list:
    file_path = os.path.join(macro_dir, macro_name, f"{macro_name}_raw.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_presets(preset_file: str) -> Dict[str, list]:
    data = read_json_file(preset_file, {})
    if isinstance(data, dict):
        return data
    return {}


def save_presets(preset_file: str, presets: Dict[str, list]) -> None:
    write_json_file(preset_file, presets)


def serialize_steps(steps: List[SequenceStep]) -> list:
    result = []
    for step in steps:
        result.append({"macro": step.macro_name, "repeats": step.repeats})
    return result


def deserialize_steps(raw_steps: list) -> List[SequenceStep]:
    steps: List[SequenceStep] = []
    for entry in raw_steps:
        if not isinstance(entry, dict):
            continue
        macro_name = entry.get("macro")
        repeats = entry.get("repeats", 1)
        if not isinstance(macro_name, str) or not macro_name.strip():
            continue
        if repeats is not None and (not isinstance(repeats, int) or repeats < 1):
            continue
        steps.append(SequenceStep(macro_name=macro_name, repeats=repeats))
    return steps


def validate_macro_references(steps: List[SequenceStep], available_macros: set) -> bool:
    for step in steps:
        if step.macro_name not in available_macros:
            print(f'"{step.macro_name}" macro does not exist')
            return False
    return True


def display_macros(available_macros: List[str]) -> None:
    print("Available macros:")
    for idx, macro_name in enumerate(available_macros, start=1):
        print(f"{idx}: {macro_name}")


def build_new_sequence(available_macros: List[str]) -> List[SequenceStep]:
    steps: List[SequenceStep] = []

    while True:
        display_macros(available_macros)
        if steps:
            print("Press Enter with no input to finish sequence.")

        # Infinite step can only be the last step.
        if steps and steps[-1].repeats is INFINITE:
            done = read_user_input("Last step is infinite. Press Enter to finish: ")
            if done == "":
                break
            print("You can only finish now because infinite repeat must be last.")
            continue

        raw = read_user_input("Select macro number or press Enter when done: ")
        if raw == "":
            if not steps:
                print("Add at least one step before finishing.")
                continue
            break

        selected = parse_positive_int(raw)
        if selected is None or selected > len(available_macros):
            print("Invalid macro selection.")
            continue

        macro_name = available_macros[selected - 1]
        repeats = prompt_repeats(f"Repeats for '{macro_name}' (Enter=1, number, inf): ")
        steps.append(SequenceStep(macro_name=macro_name, repeats=repeats))

    return steps


def prompt_save_preset(steps: List[SequenceStep], presets: Dict[str, list], preset_file: str) -> None:
    save_choice = read_user_input("Save this sequence as a preset? (y/n): ").lower()
    if save_choice != "y":
        return

    while True:
        preset_name = read_user_input("Preset name: ")
        if not preset_name:
            print("Preset name cannot be empty.")
            continue

        if preset_name in presets:
            overwrite = read_user_input(
                f'Preset "{preset_name}" exists. Overwrite? (y/n): '
            ).lower()
            if overwrite != "y":
                continue

        presets[preset_name] = serialize_steps(steps)
        save_presets(preset_file, presets)
        print(f'Preset "{preset_name}" saved.')
        return


def load_sequence_from_preset(presets: Dict[str, list]) -> Optional[List[SequenceStep]]:
    if not presets:
        print("No saved presets found.")
        return None

    names = sorted(presets.keys())
    print("Available presets:")
    for idx, name in enumerate(names, start=1):
        print(f"{idx}: {name}")

    choice = prompt_menu_choice(len(names), "Select preset: ")
    selected_name = names[choice - 1]
    steps = deserialize_steps(presets[selected_name])

    if not steps:
        print(f'Preset "{selected_name}" is empty or invalid.')
        return None

    print(f'Loaded preset: "{selected_name}"')
    return steps


def load_single_macro_sequence(available_macros: List[str]) -> List[SequenceStep]:
    print("Available macros:")
    for idx, macro_name in enumerate(available_macros, start=1):
        print(f"{idx}: {macro_name}")

    choice = prompt_menu_choice(len(available_macros), "Select macro: ")
    selected_macro = available_macros[choice - 1]
    print(f'Loaded macro: "{selected_macro}"')
    return [SequenceStep(macro_name=selected_macro, repeats=1)]


def configure_steps_playback(available_macros: List[str], preset_file: str) -> List[SequenceStep]:
    presets = load_presets(preset_file)

    while True:
        print("1: Load saved sequence")
        print("2: Load macro")
        mode_choice = prompt_menu_choice(2, "Choose option: ")

        if mode_choice == 1:
            loaded = load_sequence_from_preset(presets)
            if loaded is None:
                continue
            if not validate_macro_references(loaded, set(available_macros)):
                continue
            return loaded

        return load_single_macro_sequence(available_macros)


def configure_steps_create(available_macros: List[str], preset_file: str) -> List[SequenceStep]:
    presets = load_presets(preset_file)
    built = build_new_sequence(available_macros)
    prompt_save_preset(built, presets, preset_file)
    return built


def configure_plan(available_macros: List[str], preset_file: str, startup_mode: str) -> PlaybackPlan:
    if startup_mode == "configure":
        steps = configure_steps_create(available_macros, preset_file)
    else:
        steps = configure_steps_playback(available_macros, preset_file)

    sequence_loops = prompt_repeats(
        "Repeat full sequence (Enter=1, number, inf): "
    )
    return PlaybackPlan(steps=steps, sequence_loops=sequence_loops)


def load_events_for_steps(macro_dir: str, steps: List[SequenceStep]) -> Dict[str, list]:
    events_by_macro: Dict[str, list] = {}
    for step in steps:
        if step.macro_name in events_by_macro:
            continue
        events_by_macro[step.macro_name] = load_macro_events(macro_dir, step.macro_name)
    return events_by_macro


def read_control_commands(control_file: str) -> List[str]:
    if not os.path.exists(control_file):
        return []

    try:
        with open(control_file, "r", encoding="utf-8") as f:
            commands = [line.strip() for line in f.readlines() if line.strip()]
    except PermissionError:
        return []

    if not commands:
        return []

    try:
        open(control_file, "w", encoding="utf-8").close()
    except PermissionError:
        pass

    return commands


def main() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    macro_dir = os.path.join(root_dir, "Macros")
    control_file = os.path.join(root_dir, "control.txt")
    preset_file = os.path.join(root_dir, "sequence_presets.json")
    startup_mode = "playback"
    if len(sys.argv) >= 3 and sys.argv[1] == "--mode":
        startup_mode = sys.argv[2].strip().lower()
    if startup_mode not in {"playback", "configure"}:
        startup_mode = "playback"

    os.makedirs(macro_dir, exist_ok=True)
    clear_input_buffer()

    available_macros = get_available_macros(macro_dir)
    if not available_macros:
        print("No macros found. Record a macro first.")
        return

    plan = configure_plan(available_macros, preset_file, startup_mode)
    events_by_macro = load_events_for_steps(macro_dir, plan.steps)

    print("")
    print("Configured sequence:")
    for idx, step in enumerate(plan.steps, start=1):
        repeats_text = "inf" if step.repeats is INFINITE else str(step.repeats)
        print(f"{idx}. {step.macro_name} x{repeats_text}")
    if plan.sequence_loops is INFINITE:
        print("Full sequence loops: inf")
    else:
        print(f"Full sequence loops: {plan.sequence_loops}")
    print("Ready (Ctrl + Shift + 0 to start/stop)")

    player = SequencePlayer(
        plan=plan,
        events_by_macro=events_by_macro,
        mouse=MouseController(),
        keyboard_ctrl=KeyboardController(),
    )

    while True:
        commands = read_control_commands(control_file)
        for cmd in commands:
            if cmd == "play_start":
                player.start()
            elif cmd == "play_stop":
                player.stop()
            elif cmd == "play_toggle":
                if player.playing:
                    player.stop()
                else:
                    player.start()

        player.step()
        time.sleep(0.001)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
