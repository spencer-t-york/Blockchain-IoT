from config import ADMIN_KEY
import hashlib, json, time, os
import hmac


def sign_block(block_hash):
    return hmac.new(
        ADMIN_KEY.encode(),
        block_hash.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_admin_sig(block):
    if block["status"] not in ("APPROVED", "REVOKED"):
        return True  # PENDING blocks don't need a sig
    expected = sign_block(block["hash"])
    return hmac.compare_digest(expected, block.get("admin_sig", ""))


CHAIN_FILE = "chain.json"


def load_chain():
    if os.path.exists(CHAIN_FILE):
        return json.load(open(CHAIN_FILE))
    return []


def save_chain(chain):
    json.dump(chain, open(CHAIN_FILE, "w"), indent=2)


def make_block(chain, device_id, cert_hash, status, admin_sig=None):
    prev_hash = chain[-1]["hash"] if chain else "0" * 64
    block = {
        "index": len(chain),
        "timestamp": time.time(),
        "device_id": device_id,
        "cert_hash": cert_hash,
        "status": status,
        "admin_sig": admin_sig,
        "prev_hash": prev_hash,
    }
    block["hash"] = hashlib.sha256(
        json.dumps(block, sort_keys=True).encode()
    ).hexdigest()
    return block


def add_block(device_id, cert_hash, status, admin_sig=None):
    chain = load_chain()
    block = make_block(chain, device_id, cert_hash, status, admin_sig)
    chain.append(block)
    save_chain(chain)
    return block


def verify_device(device_id, cert_hash):
    chain = load_chain()
    # Walk chain in reverse — latest status wins
    for block in reversed(chain):
        if block["device_id"] == device_id:
            if block["cert_hash"] != cert_hash:
                return "HASH_MISMATCH"
            return block["status"]
    return "UNKNOWN"


def is_chain_valid(chain):
    for i in range(1, len(chain)):
        b = chain[i]
        check = {k: v for k, v in b.items() if k != "hash"}
        if b["hash"] != hashlib.sha256(
            json.dumps(check, sort_keys=True).encode()
        ).hexdigest():
            return False
        if b["prev_hash"] != chain[i-1]["hash"]:
            return False
    return True
