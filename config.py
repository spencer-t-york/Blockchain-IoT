from dotenv import load_dotenv
import os, hashlib

load_dotenv()

DEVICE_ID    = os.getenv("DEVICE_ID")
DEVICE_IP    = os.getenv("DEVICE_IP")
MQTT_BROKERS = os.getenv("PEER_IPS").split(",")
MQTT_PORT    = int(os.getenv("MQTT_PORT", 1883))

def get_token_hash():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    token = open(os.path.join(base_dir, "identity.token"), "r").read().strip()
    return hashlib.sha256(token.encode()).hexdigest()
