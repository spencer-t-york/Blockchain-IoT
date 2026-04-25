import secrets, hashlib, json, time

# generate tokens for all 3 Pis
tokens = {
    "pi1": secrets.token_hex(32),
    "pi2": secrets.token_hex(32),
    "pi3": secrets.token_hex(32),
}

# display tokens to copy over manually to each device
for device, token in tokens.items():
    print(f"{device} token: {token}")

# hash each token to the genesis block registry
registry = {
    device: hashlib.sha256(token.encode()).hexdigest()
    for device, token in tokens.items()
}

# save Pi 1's raw token locally
open("identity.token", "w").write(tokens["pi1"])

# build genesis block
genesis = {
    "index": 0,
    "type": "GENESIS",
    "device_id": "pi1",
    "status": "APPROVED",
    "registry": registry,
    "timestamp": time.time(),
    "prev_hash": "0" * 64,
}
genesis["hash"] = hashlib.sha256(
    json.dumps(genesis, sort_keys=True).encode()
).hexdigest()

# add genesis block to the chain
json.dump([genesis], open("chain.json", "w"), indent=2)
print("\nGenesis block written to chain.json")
