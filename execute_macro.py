import json
import time
import os
import msvcrt
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

# ====== INPUT BUFFER FIX ======
def clear_input_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()

# ====== PATH ======
root_dir = os.path.dirname(os.path.abspath(__file__))
macro_dir = os.path.join(root_dir, "macros")
os.makedirs(macro_dir, exist_ok=True)

control_file = os.path.join(root_dir, "control.txt")

# ====== SELECT MACRO ======
folders = [f for f in os.listdir(macro_dir) if os.path.isdir(os.path.join(macro_dir, f))]

for i, folder in enumerate(folders):
    print(f"{i + 1}: {folder}")

clear_input_buffer()
choice = int(input("Select macro: "))

macro_name = folders[choice - 1]
macro_folder = os.path.join(macro_dir, macro_name)
file_path = os.path.join(macro_folder, f"{macro_name}_raw.json")

print(f"\nMacro: {macro_name}")
print("Ready (CTRL + Shift + 0 to start/stop)")

# ====== LOAD EVENTS ======
with open(file_path, "r") as f:
    events = json.load(f)

# ====== CONTROLLERS ======
mouse = MouseController()
keyboard_ctrl = KeyboardController()

# ====== STATE ======
playing = False
event_index = 0
last_event_time = time.time()

# ====== KEY PARSER ======
def parse_key(key_str):
    try:
        return getattr(Key, key_str)
    except AttributeError:
        return key_str

# ====== SINGLE STEP EXECUTION ======
def play_step():
    global event_index, last_event_time

    if not events:
        return

    # Loop back to start
    if event_index >= len(events):
        event_index = 0

    event = events[event_index]

    # Wait until delay has passed
    if time.time() - last_event_time < event.get("delay", 0):
        return

    last_event_time = time.time()

    # Execute event
    if event["type"] == "move":
        mouse.position = (event["x"], event["y"])

    elif event["type"] == "click":
        btn = Button.left if "left" in event["button"] else Button.right

        if event["pressed"]:
            mouse.press(btn)
        else:
            mouse.release(btn)

    elif event["type"] == "key":
        key = parse_key(event["key"])

        if event["action"] == "down":
            keyboard_ctrl.press(key)
        elif event["action"] == "up":
            keyboard_ctrl.release(key)
    elif event["type"] == "noop":
        pass

    event_index += 1

# ====== CONTROL ======
def check_control():
    global playing, event_index, last_event_time

    if not os.path.exists(control_file):
        return

    # SAFE READ
    try:
        with open(control_file, "r") as f:
            lines = f.readlines()
    except PermissionError:
        return

    if not lines:
        return

    for cmd in lines:
        cmd = cmd.strip()

        if cmd == "play_start":
            playing = True
            event_index = 0
            last_event_time = time.time()
            print("▶️ Playing macro...")

        elif cmd == "play_stop":
            playing = False
            print("⏹️ Playback stopped.")

    # SAFE CLEAR
    try:
        open(control_file, "w").close()
    except PermissionError:
        pass

# ====== MAIN LOOP ======
while True:
    check_control()

    if playing:
        play_step()

    time.sleep(0.000)