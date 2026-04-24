import json
import os
import time
import msvcrt
from dataclasses import dataclass
from typing import List, Optional

from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button, Controller as MouseController


@dataclass
class MacroClip:
    name: str
    events: list


@dataclass
class PlaybackPlan:
    clips: List[MacroClip]
    target_chain_runs: Optional[int]  # None means run indefinitely


class MacroChainPlayer:
    def __init__(self, plan: PlaybackPlan, mouse: MouseController, keyboard_ctrl: KeyboardController):
        self.plan = plan
        self.mouse = mouse
        self.keyboard_ctrl = keyboard_ctrl

        self.playing = False
        self.clip_index = 0
        self.event_index = 0
        self.chain_runs_completed = 0
        self.last_event_time = time.time()

    def start(self) -> None:
        self.playing = True
        self.clip_index = 0
        self.event_index = 0
        self.chain_runs_completed = 0
        self.last_event_time = time.time()
        print("Playback started.")

    def stop(self, reason: str = "Playback stopped.") -> None:
        if self.playing:
            print(reason)
        self.playing = False

    def step(self) -> None:
        if not self.playing or not self.plan.clips:
            return

        clip = self.plan.clips[self.clip_index]
        if not clip.events:
            self._advance_clip()
            return

        if self.event_index >= len(clip.events):
            self._advance_clip()
            return

        event = clip.events[self.event_index]

        if time.time() - self.last_event_time < event.get("delay", 0):
            return

        self.last_event_time = time.time()
        self._execute_event(event)
        self.event_index += 1

    def _advance_clip(self) -> None:
        self.clip_index += 1
        self.event_index = 0
        self.last_event_time = time.time()

        if self.clip_index < len(self.plan.clips):
            return

        self.clip_index = 0
        self.chain_runs_completed += 1

        if self.plan.target_chain_runs is not None and self.chain_runs_completed >= self.plan.target_chain_runs:
            self.stop("Playback complete: target chain runs reached.")

    def _execute_event(self, event: dict) -> None:
        event_type = event.get("type")

        if event_type == "move":
            self.mouse.position = (event["x"], event["y"])
            return

        if event_type == "click":
            button_text = event.get("button", "")
            button = Button.left if "left" in button_text else Button.right

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

        # "noop" and unknown types are intentionally ignored.


def clear_input_buffer() -> None:
    while msvcrt.kbhit():
        msvcrt.getch()


def parse_key(key_str: str):
    try:
        return getattr(Key, key_str)
    except AttributeError:
        return key_str


def read_int(prompt: str, minimum: int = 1) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value >= minimum:
                return value
        except ValueError:
            pass
        print(f"Please enter a whole number >= {minimum}.")


def load_macro_events(macro_dir: str, macro_name: str) -> list:
    macro_folder = os.path.join(macro_dir, macro_name)
    file_path = os.path.join(macro_folder, f"{macro_name}_raw.json")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_chain_selection(raw: str, total: int) -> List[int]:
    pieces = [part.strip() for part in raw.split(",") if part.strip()]
    if not pieces:
        return []

    selected = []
    for piece in pieces:
        value = int(piece)
        if value < 1 or value > total:
            raise ValueError("Selection contains out-of-range values.")
        selected.append(value - 1)
    return selected


def build_playback_plan(macro_dir: str) -> PlaybackPlan:
    folders = sorted(
        [f for f in os.listdir(macro_dir) if os.path.isdir(os.path.join(macro_dir, f))]
    )

    if not folders:
        raise RuntimeError("No macro folders found. Record a macro first.")

    print("Available macros:")
    for i, folder in enumerate(folders, start=1):
        print(f"{i}: {folder}")

    print("")
    print("Build a chain by entering macro numbers in order, comma-separated.")
    print("Example: 1,3,2,3")

    chain_indices: List[int] = []
    while not chain_indices:
        raw = input("Chain selection: ").strip()
        try:
            chain_indices = parse_chain_selection(raw, len(folders))
        except ValueError:
            print("Invalid selection. Use numbers from the list, separated by commas.")

    clips: List[MacroClip] = []
    for idx in chain_indices:
        macro_name = folders[idx]
        events = load_macro_events(macro_dir, macro_name)
        clips.append(MacroClip(name=macro_name, events=events))

    target_runs: Optional[int]
    while True:
        run_input = input(
            "How many times should the full chain run? (number or 'inf'): "
        ).strip().lower()

        if run_input in {"inf", "infinite", "indefinite"}:
            target_runs = None
            break

        try:
            parsed = int(run_input)
            if parsed >= 1:
                target_runs = parsed
                break
        except ValueError:
            pass

        print("Enter a whole number >= 1, or 'inf'.")

    return PlaybackPlan(clips=clips, target_chain_runs=target_runs)


def read_control_commands(control_file: str) -> List[str]:
    if not os.path.exists(control_file):
        return []

    try:
        with open(control_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except PermissionError:
        return []

    if not lines:
        return []

    try:
        open(control_file, "w", encoding="utf-8").close()
    except PermissionError:
        pass

    return lines


def main() -> None:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    macro_dir = os.path.join(root_dir, "macros")
    control_file = os.path.join(root_dir, "control.txt")
    os.makedirs(macro_dir, exist_ok=True)

    clear_input_buffer()
    plan = build_playback_plan(macro_dir)

    print("")
    print("Chain configured:")
    print(" -> ".join(clip.name for clip in plan.clips))
    if plan.target_chain_runs is None:
        print("Run mode: indefinite")
    else:
        print(f"Run mode: {plan.target_chain_runs} chain run(s)")
    print("Ready (Ctrl + Shift + 0 to start/stop)")

    mouse = MouseController()
    keyboard_ctrl = KeyboardController()
    player = MacroChainPlayer(plan, mouse, keyboard_ctrl)

    while True:
        commands = read_control_commands(control_file)
        for cmd in commands:
            if cmd == "play_start":
                player.start()
            elif cmd == "play_stop":
                player.stop()

        player.step()
        time.sleep(0.001)


if __name__ == "__main__":
    main()
