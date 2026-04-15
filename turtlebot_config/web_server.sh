#!/bin.bash

TURTLEBOT_NAME=$(hostname)
IP_ADDR=$(hostname -I)

# must add env variable for SERVER_URL

# wait for dashboard to be reachable
echo "Waiting for dashboard..."
for i in {1..15}; do
    if curl -s --max-time 2 "${SERVER_URL}" > /dev/null 2>&1; then
        echo "Dashboard reachable!"
        break
    fi
    echo "  Attempt $i/15..."
    sleep 1
done

# post to dashboard
curl -s -X POST "${SERVER_URL}/devices" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${TURTLEBOT_NAME}\", \"ip\": \"${IP_ADDR}\"}" > /dev/null 2>&1

echo "posted ${TURTLEBOT_NAME} at ${IP_ADDR} to ${SERVER_URL}"
exit 0