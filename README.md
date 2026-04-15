# Turtlebot Dashboard (Flask Version)

A Flask-based web dashboard for managing and monitoring Turtlebot Raspberry Pis.

## Features

- **Web Dashboard**: Real-time turtlebot status monitoring
- **WebSocket Updates**: Live updates without page refresh
- **Device Tracking**: Monitor IP addresses, DNS status, and last connection time
- **REST API**: JSON endpoints for device management

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask server:**
   ```bash
   python app.py
   ```

3. **Access the dashboard:**
   - Open `http://rbe-turtlebots.dyn.wpi.edu:5000` in your browser

## TurtleBot Configuration

Example bash script to run at boot (add to .bashrc):
```bash
#!/bin/bash

# Wait for dashboard to be reachable
echo "Waiting for dashboard..."
for i in {1..15}; do
    if curl -s --max-time 2 "${SERVER_URL}" > /dev/null 2>&1; then
        echo "Dashboard reachable!"
        break
    fi
    echo "  Attempt $i/15..."
    sleep 1
done

# Post to dashboard
curl -X POST "${SERVER_URL}/devices" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${TURTLEBOT_NAME}\", \"ip\": \"${IP_ADDR}\"}"

echo "posted ${TURTLEBOT_NAME} at ${IP_ADDR} to ${SERVER_URL}"
exit 0
```

## API Endpoints

### GET /devices
Returns all registered turtlebots.

**Response:**
```json
[
  {
    "name": "mario",
    "ip": "192.168.1.100",
    "dns": "Y",
    "lastConnected": "2026-04-15 14:30:45"
  }
]
```

### POST /devices
Update a turtlebot's information.

**Request:**
```json
{
  "name": "mario",
  "ip": "192.168.1.105",
  "dns": "Y"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Device updated successfully"
}
```

## WebSocket Events

The dashboard uses WebSocket (Socket.IO) for real-time updates.

### Server Events
- `update`: Sent when a device is updated
- `devices_update`: Sent when requesting full device list

### Client Events
- `request_update`: Request full device list from server

## Add/Remove Turtlebots

Edit `static/turtlebots.txt` in this format:
```
name,ip,dns_status,last_connected
mario,,N,
luigi,,N,
```
Or use the POST /devices endpoint to add turtlebots dynamically.
> Make sure they are in order so that the `number` column is correct

## Project Structure

```
turtlebot_esp32/
├── app.py                       # Flask application
├── requirements.txt             # Python dependencies
├── templates/index.html         # Dashboard template
├── static/
│   ├── css/style.css           # Terminal-style CSS
│   └── js/actions.js           # WebSocket client
└── .old_files/                 # Original ESP32 files (archived)
```

## Original Implementation (ESP32)
The ESP32 C++ implementation is archived in the branch `esp-32` for reference.