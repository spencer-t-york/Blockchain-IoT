import socket, json, threading
from chain import load_chain, save_chain, is_chain_valid
from config import PEERS, GOSSIP_PORT

def broadcast_chain():
    chain = load_chain()
    payload = json.dumps(chain).encode()
    for peer in PEERS:
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((peer, GOSSIP_PORT))
            s.sendall(payload)
            s.close()
        except:
            pass  # peer offline — skip, try next broadcast

def listen_for_gossip():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", GOSSIP_PORT))
    srv.listen(5)
    while True:
        conn, _ = srv.accept()
        data = b""
        while chunk := conn.recv(4096):
            data += chunk
        conn.close()
        try:
            incoming = json.loads(data)
            local = load_chain()
            if len(incoming) > len(local) and is_chain_valid(incoming):
                save_chain(incoming)
                print("Chain updated via gossip")
        except:
            pass

def start_gossip_listener():
    t = threading.Thread(target=listen_for_gossip, daemon=True)
    t.start()
