import hashlib, subprocess, socket

DEVICE_ID = socket.gethostname()  # pi1

PEERS = [
    "192.168.40.74",  # pi2
    "192.168.40.73",  # pi3
]  # remove this Pi's own IP from the list

GOSSIP_PORT = 5001
ADMIN_PORT  = 5000
MQTT_BROKER = "192.168.40.73"  # Pi3 runs mosquitto

def get_cert_hash():
    cert = open("/iot-trust/device.crt", "rb").read()
    return hashlib.sha256(cert).hexdigest()
ADMIN_KEY = "96dd7c00b6b94f7e2d193ef0ec3df095572323d2c8819a6c7df2446fb8023433"
