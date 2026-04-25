from dotenv import load_dotenv
import os

load_dotenv()

peers = os.getenv("PEER_IPS").split(",")
port  = os.getenv("MQTT_PORT", 1883)

config_lines = []
for i, ip in enumerate(peers):
    config_lines.append(f"connection bridge-to-{ip}")
    config_lines.append(f"address {ip}:{port}")
    config_lines.append(f"topic # both 0")
    config_lines.append("")

output = "\n".join(config_lines)

with open("/etc/mosquitto/conf.d/bridge.conf", "w") as f:
    f.write(output)

print("Bridge config written:")
print(output)
