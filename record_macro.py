import json
import time
import os
import tkinter as tk
from pynput import mouse
import keyboard as kb

# ====== STATE ======
recording = False
events = []
last_event_time = None

# ====== PATH ======
root_dir = os.path.dirname(os.path.abspath(__file__))
macro_dir = os.path.join(root_dir, "macros")
os.makedirs(macro_dir, exist_ok=True)

control_file = os.path.join(root_dir, "control.txt")
mouse_controller = mouse.Controller()


def read_user_input(prompt_text):
    print("")
    return input(prompt_text).strip()

# ====== COUNTDOWN POPUP ======
def countdown_popup(seconds=3):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int(screen_width / 2 - 50)
    y = int(screen_height / 2 - 50)
    root.geometry(f"100x100+{x}+{y}")

    label = tk.Label(root, text="", font=("Arial", 40))
    label.pack(expand=True)

    def update(count):
        if count > 0:
            label.config(text=str(count))
            root.after(1000, update, count - 1)
        else:
            root.destroy()

    update(seconds)
    root.mainloop()

# ====== TIME ======
def get_delay():
    global last_event_time
    now = time.time()

    if last_event_time is None:
        delay = 0
    else:
        delay = now - last_event_time

    last_event_time = now
    return delay

# ====== MOUSE ======
def on_move(x, y):
    if recording:
        events.append({
            "type": "move",
            "x": x,
            "y": y,
            "delay": get_delay()
        })

def on_click(x, y, button, pressed):
    if recording:
        events.append({
            "type": "click",
            "x": x,
            "y": y,
            "button": str(button),
            "pressed": pressed,
            "delay": get_delay()
        })

# ====== KEYBOARD ======
def on_key_event(event):
    if not recording:
        return

    events.append({
        "type": "key",
        "key": event.name,
        "action": event.event_type,
        "delay": get_delay()
    })

# ====== 🔥 CONTROL HOTKEY CLEANUP ======
def remove_control_hotkey_sequences(events):
    cleaned = []
    i = 0

    while i < len(events):
        # Detect CTRL + SHIFT + 0 (0 may appear as ")")
        if (
            i + 2 < len(events)
            and events[i]["type"] == "key"
            and events[i]["key"] in ("ctrl", "ctrl_l", "ctrl_r")
            and events[i]["action"] == "down"

            and events[i+1]["type"] == "key"
            and events[i+1]["key"] in ("shift", "shift_l", "shift_r")
            and events[i+1]["action"] == "down"

            and events[i+2]["type"] == "key"
            and events[i+2]["key"] in ("0", ")")
            and events[i+2]["action"] == "down"
        ):
            # 🚫 Skip this sequence
            i += 3
            continue

        cleaned.append(events[i])
        i += 1

    return cleaned

# ====== CONTROL ======
def check_control():
    global recording, events, last_event_time

    if not os.path.exists(control_file):
        return

    with open(control_file, "r") as f:
        cmd = f.read().strip()

    # ===== START =====
    if cmd == "record_start" and not recording:
        countdown_popup(3)

        recording = True
        events = []
        start_x, start_y = mouse_controller.position
        events.append({
            "type": "move",
            "x": start_x,
            "y": start_y,
            "delay": 0
        })
        last_event_time = time.time()

        print("🔴 Recording started.")

    # ===== STOP =====
    elif cmd == "record_stop" and recording:
        recording = False
        print("🟢 Recording stopped.")

        # 🔥 CLEAN THE DATA HERE
        cleaned_events = remove_control_hotkey_sequences(events)

        choice = read_user_input("Save recording? (y/n): ").lower()

        if choice == "y":
            filename = read_user_input("Enter macro name: ") or "macro"

            macro_folder = os.path.join(macro_dir, filename)
            os.makedirs(macro_folder, exist_ok=True)

            raw_path = os.path.join(macro_folder, f"{filename}_raw.json")

            with open(raw_path, "w") as f:
                json.dump(cleaned_events, f, indent=2)

            print(f"✅ Saved to: {raw_path}")
        else:
            print("❌ Recording discarded.")

    # Clear control file
    open(control_file, "w").close()

# ====== START LISTENERS ======
mouse.Listener(on_move=on_move, on_click=on_click).start()
kb.hook(on_key_event)

print("Waiting for commands...")

# ====== LOOP ======
while True:
    check_control()
    time.sleep(0.05)
