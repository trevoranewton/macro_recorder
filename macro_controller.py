import os
import subprocess
from pynput import keyboard


base_dir = os.path.dirname(os.path.abspath(__file__))
record_script = os.path.join(base_dir, "record_macro.py")
execute_script = os.path.join(base_dir, "execute_macro.py")
control_file = os.path.join(base_dir, "control.txt")

record_process = None
execute_process = None
mode = None  # "record" or "play"
active = False  # record mode toggle state


def write_command(cmd: str) -> None:
    with open(control_file, "a", encoding="utf-8") as f:
        f.write(cmd + "\n")


def start_execute_process(start_mode: str, restart: bool) -> None:
    global execute_process

    if restart and execute_process:
        execute_process.terminate()
        execute_process = None

    if execute_process and execute_process.poll() is not None:
        execute_process = None

    if execute_process is None:
        execute_process = subprocess.Popen(
            ["python", execute_script, "--mode", start_mode],
            cwd=base_dir,
        )


def set_record_mode() -> None:
    global mode, record_process, execute_process, active

    if mode == "record":
        return

    print("\nRECORD MODE")
    print("Press CTRL + Shift + 0 to start/stop recording")

    mode = "record"
    active = False

    if execute_process:
        execute_process.terminate()
        execute_process = None

    if record_process:
        record_process.terminate()

    record_process = subprocess.Popen(["python", record_script], cwd=base_dir)


def set_play_mode() -> None:
    global mode, record_process, active

    print("\nPLAYBACK MODE")

    mode = "play"
    active = False

    if record_process:
        record_process.terminate()
        record_process = None

    # Keep current playback config if already loaded.
    start_execute_process(start_mode="playback", restart=False)


def set_configure_sequence_mode() -> None:
    global mode, record_process, active

    print("\nCONFIGURE SEQUENCE MODE")

    mode = "play"
    active = False

    if record_process:
        record_process.terminate()
        record_process = None

    # Always restart to reopen config flow.
    start_execute_process(start_mode="configure", restart=True)


def toggle_action() -> None:
    global active

    if mode is None:
        return

    if mode == "record":
        write_command("record_start" if not active else "record_stop")
        active = not active
    elif mode == "play":
        write_command("play_toggle")


print("Pipeline Controller Running")
print("CTRL + Shift + 1 -> Record Mode")
print("CTRL + Shift + 2 -> Playback Mode")
print("CTRL + Shift + 3 -> Configure Sequence Mode")

try:
    with keyboard.GlobalHotKeys(
        {
            "<ctrl>+<shift>+1": set_record_mode,
            "<ctrl>+<shift>+2": set_play_mode,
            "<ctrl>+<shift>+3": set_configure_sequence_mode,
            "<ctrl>+<shift>+0": toggle_action,
        }
    ) as hotkeys:
        hotkeys.join()

except KeyboardInterrupt:
    print("\nShutting down...")

    if record_process:
        record_process.terminate()

    if execute_process:
        execute_process.terminate()
