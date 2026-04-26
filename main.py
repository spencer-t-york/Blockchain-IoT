import time, os, atexit, socket
from mqtt_client import start, publish_chain, publish_pending
from chain import load_chain, get_device_status
from config import DEVICE_ID, MQTT_BROKERS, MQTT_PORT
from led import set_led, cleanup


GENESIS_PI = "pi1"  # only this Pi has the genesis block


def wait_for_network(host, port, interval=2):
    print(f"[{DEVICE_ID}] Waiting for network...")
    while True:
        try:
            socket.setdefaulttimeout(2)
            socket.socket().connect((host, port))
            print(f"[{DEVICE_ID}] Network ready")
            return
        except OSError:
            time.sleep(interval)


def boot():
    set_led("UNKNOWN")
    print(f"[{DEVICE_ID}] Booting — waiting for network...")
    wait_for_network(MQTT_BROKERS[0], MQTT_PORT)

    start()
    print(f"[{DEVICE_ID}] MQTT started, waiting for chain...")

    if DEVICE_ID == GENESIS_PI:
        print(f"[{DEVICE_ID}] Genesis node — publishing chain")
        publish_chain()
    else:
        # Wait until chain actually arrives via MQTT
        while not load_chain():
            time.sleep(0.5)
        print(f"[{DEVICE_ID}] Chain received")

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
