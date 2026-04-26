import time, os, atexit
from mqtt_client import start, publish_chain, publish_pending
from chain import load_chain, get_device_status
from config import DEVICE_ID
from led import set_led, cleanup

GENESIS_PI = "pi1"  # only this Pi has the genesis block

def boot():
    set_led("UNKNOWN")
    print(f"[{DEVICE_ID}] Booting — waiting for network...")
    time.sleep(15)

    # Start MQTT — subscribe first before doing anything
    start()
    print(f"[{DEVICE_ID}] MQTT started, waiting for chain...")
    time.sleep(5)

    chain = load_chain()

    # Pi 1 — publish genesis chain so others can sync
    if DEVICE_ID == GENESIS_PI:
        print(f"[{DEVICE_ID}] Genesis node — publishing chain")
        publish_chain()
        time.sleep(2)

    # Check own status
    chain = load_chain()
    status = get_device_status(DEVICE_ID, chain)
    print(f"[{DEVICE_ID}] Current status: {status}")
    set_led(status)

    if status == "APPROVED":
        print(f"[{DEVICE_ID}] Already approved, joining network")
    else:
        print(f"[{DEVICE_ID}] Not approved, registering as PENDING")
        publish_pending()

    # Keep running
    print(f"[{DEVICE_ID}] Node running")
    while True:
        chain = load_chain()
        status = get_device_status(DEVICE_ID, chain)
        set_led(status)
        time.sleep(5)

if __name__ == "__main__":
    boot()
