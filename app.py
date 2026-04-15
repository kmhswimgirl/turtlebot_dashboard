from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# add database later
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

# load on startup
load_devices_from_file()

def check_dns_status(turtlebot_name):
    """Check if a turtlebot DNS name can be resolved"""
    if not turtlebot_name:
        return 'N'
    
    hostname = f"{turtlebot_name}.dyn.wpi.edu"
    
    try:
        result = subprocess.run(['nslookup', hostname], 
                              timeout=2, capture_output=True)
        status = 'Y' if result.returncode == 0 else 'N'
        print(f"  DNS {hostname}: {status}")
        return status
    except Exception as e:
        print(f"  DNS {hostname}: ERROR - {e}")
        return 'N'
    
# ping all turtlebots immediately on startup
def ping_all_turtlebots():
    """Ping all turtlebots and update DNS status"""
    global devices
    print("pinging all turtlebot DNS...")
    
    for name in devices:
        old_dns = devices[name]['dns']
        new_dns = check_dns_status(name)
        
        if old_dns != new_dns:
            devices[name]['dns'] = new_dns
            print(f"  {name}: DNS {old_dns} → {new_dns}")
            
            # Broadcast update to all connected clients
            socketio.emit('update', {'device': devices[name]})

# startup ping
print("Starting initial DNS check...")
ping_all_turtlebots()

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
        
        if 'ip' in data:
            devices[name]['ip'] = data['ip']
            devices[name]['dns'] = check_dns_status(name)
        elif 'dns' in data:
            devices[name]['dns'] = data['dns']
        
        devices[name]['lastConnected'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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

# background scheduling
scheduler = BackgroundScheduler()
scheduler.add_job(ping_all_turtlebots, 'interval', minutes=1)

if __name__ == "__main__":
    # startup ping
    print("starting initial DNS check...")
    ping_all_turtlebots()
    
    scheduler.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
