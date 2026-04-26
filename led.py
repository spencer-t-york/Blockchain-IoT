import sys

LED_LINES = 4
_initialized = False

def set_led(status, device_id=""):
    global _initialized

    if status == "APPROVED":
        color = "\033[92m"
        label = "TRUSTED"
    elif status == "PENDING":
        color = "\033[93m"
        label = "PENDING"
    else:
        color = "\033[91m"
        label = "UNTRUSTED"

    reset = "\033[0m"
    sub   = f"     {device_id}" if device_id else ""

    box = [
        f"{color}┌─────────────────────┐{reset}",
        f"{color}│  ◉  {label:<16}│{reset}",
        f"{color}│{sub:<23}│{reset}",
        f"{color}└─────────────────────┘{reset}",
    ]

    if not _initialized:
        # First render — just print naturally, no cursor tricks
        for line in box:
            print(line)
        print()  # blank separator before logs
        _initialized = True
    else:
        # Subsequent renders — jump back up over the box and redraw
        up = f"\033[{LED_LINES + 1}A"   # +1 for the blank separator
        print(up, end="")
        for line in box:
            print(f"\033[2K{line}")      # clear line before redrawing
        print("\033[2K")                 # clear the blank separator line too
        sys.stdout.flush()

def cleanup():
    set_led("UNKNOWN")
