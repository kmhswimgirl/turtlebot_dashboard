from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store devices in memory (add database later)
devices = {}

def load_devices_from_file():
    """Load turtlebot names from the old data file"""
    global devices
    file_path = 'static/turtlebots.txt'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                name = parts[0] if parts else ''
                if name:
                    devices[name] = {
                        'name': name,
                        'ip': parts[1] if len(parts) > 1 else '',
                        'dns': parts[2] if len(parts) > 2 else 'N',
                        'lastConnected': parts[3] if len(parts) > 3 else ''
                    }

# Load devices on startup
load_devices_from_file()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/devices", methods=["GET"])
def get_devices():
    """Return all devices as JSON"""
    return jsonify(list(devices.values())), 200

@app.route("/devices", methods=["POST"])
def update_device():
    """Update a device with new data (IP, DNS status, etc.)"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        name = data.get('name')
        
        if name not in devices:
            return jsonify({"status": "error", "message": "Device not found"}), 404
        
        # Update only provided fields
        if 'ip' in data:
            devices[name]['ip'] = data['ip']
        if 'dns' in data:
            devices[name]['dns'] = data['dns']
        
        # Update last connected timestamp
        devices[name]['lastConnected'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Broadcast update to all connected clients
        socketio.emit('update', {'device': devices[name]})
        
        return jsonify({
            "status": "success",
            "message": "Device updated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to Turtlebot Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_update')
def handle_request_update():
    """Client requested a full device list update"""
    emit('devices_update', {'devices': list(devices.values())}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
