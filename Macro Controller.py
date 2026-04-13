import subprocess
import os
from pynput import keyboard

# ====== PATHS ======
base_dir = os.path.dirname(os.path.abspath(__file__))

macro_dir = os.path.join(base_dir, "macros")
os.makedirs(macro_dir, exist_ok=True)

record_script = os.path.join(base_dir, "Record Macro.py")
execute_script = os.path.join(base_dir, "Exectue Macro.py")
control_file = os.path.join(base_dir, "control.txt")

record_process = None
execute_process = None
mode = None  # "record" or "play"
active = False  # whether currently running action

# ====== WRITE COMMAND ======
def write_command(cmd):
    with open(control_file, "w") as f:
        f.write(cmd)

# ====== MODE SWITCHING ======
def set_record_mode():
    global mode, record_process, execute_process, active

    # 🚫 Prevent re-trigger if already in record mode
    if mode == "record":
        return

    print("\n🔁 RECORD MODE")
    print("Press CTRL + Shift + 0 to start/stop recording")

    mode = "record"
    active = False

    # Stop playback process if running
    if execute_process:
        execute_process.terminate()
        execute_process = None

    # Start recorder fresh
    if record_process:
        record_process.terminate()

    record_process = subprocess.Popen(["python", record_script], cwd=base_dir)

def set_play_mode():
    global mode, record_process, execute_process, active

    # 🚫 Prevent re-trigger if already in play mode
    if mode == "play":
        return

    print("\n🔁 PLAYBACK MODE")

    mode = "play"
    active = False

    # Stop recording process if running
    if record_process:
        record_process.terminate()
        record_process = None

    # Start executor fresh
    if execute_process:
        execute_process.terminate()

    execute_process = subprocess.Popen(["python", execute_script], cwd=base_dir)

# ====== TOGGLE ACTION ======
def toggle_action():
    global active

    if mode is None:
        return

    if not active:
        if mode == "record":
            write_command("record_start")
        elif mode == "play":
            write_command("play_start")
        active = True
    else:
        if mode == "record":
            write_command("record_stop")
        elif mode == "play":
            write_command("play_stop")
        active = False

# ====== MAIN ======
print("Pipeline Controller Running")
print("CTRL + Shift + 1 → Record Mode")
print("CTRL + Shift + 2 → Playback Mode")

try:
    with keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+1': set_record_mode,
        '<ctrl>+<shift>+2': set_play_mode,
        '<ctrl>+<shift>+0': toggle_action
    }) as h:
        h.join()

except KeyboardInterrupt:
    print("\n🛑 Shutting down...")

    if record_process:
        record_process.terminate()

    if execute_process:
        execute_process.terminate()