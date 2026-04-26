#!/bin/bash

# Load device ID from .env
DEVICE_ID=$(grep DEVICE_ID .env | cut -d '=' -f2)

echo "Resetting $DEVICE_ID..."

# Clear retained MQTT messages
mosquitto_pub -h localhost -t iot/register -n -r
mosquitto_pub -h localhost -t iot/chain -n -r
mosquitto_pub -h localhost -t iot/vote -n -r

if [ "$DEVICE_ID" = "pi1" ]; then
    echo "Genesis node — restoring genesis block only"
    python3 -c "
import json
chain = json.load(open('chain.json'))
json.dump([chain[0]], open('chain.json', 'w'), indent=2)
print('Genesis block restored')
"
else
    echo "Non-genesis node — clearing chain"
    rm -f chain.json
fi

echo "$DEVICE_ID reset complete"
