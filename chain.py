import hashlib, json, time, math, os, threading

CHAIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chain.json")
_lock = threading.Lock()


def load_chain():
    with _lock:
        if os.path.exists(CHAIN_FILE):
            return json.load(open(CHAIN_FILE))
        return []


def save_chain(chain):
    with _lock:
        tmp = CHAIN_FILE + ".tmp"
        json.dump(chain, open(tmp, "w"), indent=2)
        os.replace(tmp, CHAIN_FILE)


def make_block(chain, **fields):
    block = {
        "index": len(chain),
        "timestamp": time.time(),
        "prev_hash": chain[-1]["hash"] if chain else "0" * 64,
        **fields
    }
    block["hash"] = hashlib.sha256(
        json.dumps(block, sort_keys=True).encode()
    ).hexdigest()
    return block


def is_chain_valid(chain):
    for i, block in enumerate(chain):
        check = {k: v for k, v in block.items() if k != "hash"}
        if block["hash"] != hashlib.sha256(
            json.dumps(check, sort_keys=True).encode()
        ).hexdigest():
            return False
        if i > 0 and block["prev_hash"] != chain[i-1]["hash"]:
            return False
    return True


def get_registry(chain):
    registry = chain[0]["registry"].copy()
    for block in chain:
        if block["type"] == "REGISTRY_UPDATE":
            registry[block["new_device_id"]] = block["new_token_hash"]
    return registry


def validate_token(token_hash, chain):
    registry = get_registry(chain)
    return token_hash in registry.values()


def get_device_status(device_id, chain):
    for block in reversed(chain):
        if block.get("device_id") == device_id:
            if block.get("type") in ("REGISTRATION", "GENESIS"):
                return block["status"]
    return "UNKNOWN"


def get_trusted_peers(chain):
    seen, trusted = set(), []
    for block in reversed(chain):
        if block.get("type") in ("REGISTRATION", "GENESIS") and block.get("status") == "APPROVED":
            if block["device_id"] not in seen:
                seen.add(block["device_id"])
                trusted.append(block["device_id"])
    return trusted


def already_voted(voter_id, device_id, chain):
    for block in chain:
        if (block.get("type") == "VOTE" and
            block.get("voter_id") == voter_id and
            block.get("device_id") == device_id):
            return True
    return False


def count_votes(device_id, chain):
    voters = set()
    for block in chain:
        if block.get("type") == "VOTE" and block.get("device_id") == device_id:
            voters.add(block["voter_id"])
    return len(voters)


def quorum_reached(device_id, chain):
    trusted = get_trusted_peers(chain)
    votes   = count_votes(device_id, chain)
    quorum  = (len(trusted) // 2) + 1
    return votes >= quorum


def add_block(chain, **fields):
    block = make_block(chain, **fields)
    chain.append(block)
    save_chain(chain)
    return block
