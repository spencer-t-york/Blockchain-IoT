import paho.mqtt.client as mqtt
import json, time, random, os
from chain import (load_chain, save_chain, is_chain_valid, add_block,
                   get_device_status, get_trusted_peers, validate_token,
                   count_votes, quorum_reached, already_voted)
from config import DEVICE_ID, MQTT_BROKERS, MQTT_PORT, get_token_hash

TOPIC_REGISTER = "iot/register"
TOPIC_VOTE     = "iot/vote"
TOPIC_CHAIN    = "iot/chain"

client = mqtt.Client()
_voted_for = set()

# ─── Publish helpers ───────────────────────────────────────────

def publish_chain():
    chain = load_chain()
    client.publish(TOPIC_CHAIN, json.dumps(chain), retain=True)
    print(f"[{DEVICE_ID}] Chain published ({len(chain)} blocks)")

def publish_pending():
    payload = json.dumps({
        "device_id": DEVICE_ID,
        "token_hash": get_token_hash()
    })
    client.publish(TOPIC_REGISTER, payload, retain=True)
    print(f"[{DEVICE_ID}] Published PENDING registration")

def publish_vote(target_device_id):
    payload = json.dumps({
        "voter_id":  DEVICE_ID,
        "device_id": target_device_id,
    })
    client.publish(TOPIC_VOTE, payload)
    print(f"[{DEVICE_ID}] Published vote for {target_device_id}")

# ─── Core vote logic ───────────────────────────────────────────

def on_vote(payload):
    voter_id  = payload["voter_id"]
    device_id = payload["device_id"]

    chain = load_chain()

    if get_device_status(device_id, chain) == "APPROVED":
        return

    if get_device_status(device_id, chain) != "PENDING":
        return

    if already_voted(voter_id, device_id, chain):
        return

    # Write vote block
    add_block(chain,
        type="VOTE",
        voter_id=voter_id,
        device_id=device_id,
    )
    chain = load_chain()
    print(f"[{DEVICE_ID}] Recorded vote from {voter_id} for {device_id}")

    # Check quorum
    if quorum_reached(device_id, chain):
        time.sleep(random.uniform(0.1, 0.9))
        chain = load_chain()
        if get_device_status(device_id, chain) == "APPROVED":
            return
        add_block(chain,
            type="REGISTRATION",
            device_id=device_id,
            token_hash=payload.get("token_hash", ""),
            status="APPROVED"
        )
        print(f"[{DEVICE_ID}] {device_id} APPROVED — quorum reached")
        publish_chain()

# ─── MQTT handlers ─────────────────────────────────────────────

def on_register(payload):
    incoming_device = payload["device_id"]
    incoming_hash   = payload["token_hash"]

    # Ignore own registration
    if incoming_device == DEVICE_ID:
        return

    # Already voted for this device
    if incoming_device in _voted_for:
        return

    chain = load_chain()

    # Only trusted devices can vote
    if get_device_status(DEVICE_ID, chain) != "APPROVED":
        return

    # Already approved — nothing to do
    if get_device_status(incoming_device, chain) == "APPROVED":
        return

    # Validate token against registry
    if not validate_token(incoming_hash, chain):
        print(f"[{DEVICE_ID}] Unknown token from {incoming_device} — ignoring")
        return

    # Write PENDING block if not already there
    if get_device_status(incoming_device, chain) == "UNKNOWN":
        add_block(chain,
            type="REGISTRATION",
            device_id=incoming_device,
            token_hash=incoming_hash,
            status="PENDING"
        )

    # Phase 1 — vote locally first
    _voted_for.add(incoming_device)
    on_vote({"voter_id": DEVICE_ID, "device_id": incoming_device})

    # Check if quorum already met locally
    chain = load_chain()
    if get_device_status(incoming_device, chain) == "APPROVED":
        return  # done, chain already published

    # Phase 2 — quorum not met, publish vote for other Pis
    publish_vote(incoming_device)

def on_chain(payload):
    incoming = payload
    local    = load_chain()

    if len(incoming) > len(local) and is_chain_valid(incoming):
        save_chain(incoming)
        print(f"[{DEVICE_ID}] Chain updated ({len(incoming)} blocks)")

# ─── MQTT callbacks ────────────────────────────────────────────

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
    except:
        return

    if msg.topic == TOPIC_REGISTER:
        on_register(payload)
    elif msg.topic == TOPIC_VOTE:
        on_vote(payload)
    elif msg.topic == TOPIC_CHAIN:
        on_chain(payload)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[{DEVICE_ID}] Disconnected, reconnecting...")
        connect()

# ─── Connection ────────────────────────────────────────────────

def connect():
    for broker in MQTT_BROKERS:
        try:
            client.connect(broker, MQTT_PORT, keepalive=60)
            print(f"[{DEVICE_ID}] Connected to broker at {broker}")
            return
        except Exception:
            print(f"[{DEVICE_ID}] Broker {broker} unreachable, trying next...")
    raise RuntimeError("No brokers available")

def start():
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    connect()

    client.subscribe([
        (TOPIC_REGISTER, 0),
        (TOPIC_VOTE,     0),
        (TOPIC_CHAIN,    0),
    ])

    client.loop_start()
    print(f"[{DEVICE_ID}] MQTT client started")
