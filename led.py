import os

_last_status = None

def set_led(status, device_id=""):
    global _last_status
    if status == _last_status:
        return

    if status == "APPROVED":
        color = "\033[92m"
        label = "● TRUSTED"
    elif status == "PENDING":
        color = "\033[93m"
        label = "● PENDING"
    else:
        color = "\033[91m"
        label = "● UNTRUSTED"

    reset = "\033[0m"
    suffix = f" ({device_id})" if device_id else ""
    print(f"{color}[STATUS] {label}{suffix}{reset}", flush=True)
    _last_status = status

def cleanup():
    set_led("UNKNOWN")
