# run once on first boot
from chain import add_block
from gossip import broadcast_chain
from config import DEVICE_ID, get_cert_hash

add_block(DEVICE_ID, get_cert_hash(), "PENDING")
broadcast_chain()
print(f"{DEVICE_ID} registered — awaiting admin approval")
