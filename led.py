import os

def set_led(status):
    # Clear terminal
    os.system('clear')
    
    if status == "APPROVED":
        print("\033[92m")  # green
        print("  ██████████████████████")
        print("  █                    █")
        print("  █   ●  GREEN         █")
        print("  █      TRUSTED       █")
        print("  █                    █")
        print("  ██████████████████████")
        print("\033[0m")
    elif status == "PENDING":
        print("\033[93m")  # yellow
        print("  ██████████████████████")
        print("  █                    █")
        print("  █   ●  YELLOW        █")
        print("  █      PENDING       █")
        print("  █                    █")
        print("  ██████████████████████")
        print("\033[0m")
    else:
        print("\033[91m")  # red
        print("  ██████████████████████")
        print("  █                    █")
        print("  █   ●  RED           █")
        print("  █      UNTRUSTED     █")
        print("  █                    █")
        print("  ██████████████████████")
        print("\033[0m")

def cleanup():
    set_led("UNKNOWN")
