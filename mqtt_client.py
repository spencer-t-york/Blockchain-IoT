import paho.mqtt.client as mqtt
import json, time, random, math, os
from chain import (load_chain, save_chain, is_chain_valid, add_block,
                   get_device_status, get_trusted_peers, validate_token,
                   count_votes, quorum_reached)
from config import DEVICE_ID, MQTT_BROKERS, MQTT_PORT, get_token_hash


# Topics
TOPIC_REGISTER = "iot/register"
TOPIC_VOTE     = "iot/vote"
TOPIC_CHAIN    = "iot/chain"

client = mqtt.Client()


# ─── Publish helpers ───────────────────────────────────────────

def publish_pending():
    payload = json.dumps({
        "device_id": DEVICE_ID,
        "token_hash": get_token_hash()
    })
    client.publish(TOPIC_REGISTER, payload, retain=True)
    print(f"[{DEVICE_ID}] Published PENDING registration")


def publish_vote(target_device_id):
    payload = json.dumps({
        "voter_id": DEVICE_ID,
        "device_id": target_device_id,
    })
    client.publish(TOPIC_VOTE, payload)
    print(f"[{DEVICE_ID}] Voted for {target_device_id}")


def publish_chain():
    chain = load_chain()
    client.publish(TOPIC_CHAIN, json.dumps(chain), retain=True)
    print(f"[{DEVICE_ID}] Chain published ({len(chain)} blocks)")


# ─── Message handlers ──────────────────────────────────────────

def on_register(payload):
    incoming_device  = payload["device_id"]
    incoming_hash    = payload["token_hash"]

    # Don't vote for yourself
    if incoming_device == DEVICE_ID:
        return

    chain = load_chain()

    # Only trusted devices can vote
    if get_device_status(DEVICE_ID, chain) != "APPROVED":
        return

    # Already approved — no need to vote
    if get_device_status(incoming_device, chain) == "APPROVED":
        return

    # Validate token hash against registry
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
        chain = load_chain()

    # Cast vote
    publish_vote(incoming_device)


def on_vote(payload):
    voter_id  = payload["voter_id"]
    device_id = payload["device_id"]

    # Don't process your own votes
    if voter_id == DEVICE_ID:
        return

    chain = load_chain()

    # Only process votes for PENDING devices
    if get_device_status(device_id, chain) != "PENDING":
        return

    # Record the vote block
    add_block(chain,
        type="VOTE",
        voter_id=voter_id,
        device_id=device_id,
    )
    chain = load_chain()

    # Check quorum
    if quorum_reached(device_id, chain):
        # Random delay to prevent duplicate APPROVED blocks
        time.sleep(random.uniform(0.1, 0.9))

        # Re-check after delay — someone else may have approved already
        chain = load_chain()
        if get_device_status(device_id, chain) == "APPROVED":
            return

        # Write APPROVED block
        add_block(chain,
            type="REGISTRATION",
            device_id=device_id,
            token_hash=payload.get("token_hash", ""),
            status="APPROVED"
        )
        print(f"[{DEVICE_ID}] {device_id} approved — quorum reached")
        publish_chain()


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

