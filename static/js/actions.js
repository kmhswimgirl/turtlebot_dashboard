// Connect to WebSocket via Socket.IO
const socket = io();

// On connection, request initial device list
socket.on('connect', function() {
    console.log('Connected to server');
    loadDevices();
});

// Listen for device updates from server
socket.on('update', function(data) {
    console.log('🔄 Device update received:', data);
    console.log('🔄 Loading devices...');
    loadDevices();
});

// Listen for full device list updates
socket.on('devices_update', function(data) {
    console.log('Full devices update received');
    updateTable(data.devices);
});

function loadDevices() {
    fetchDevicesAndUpdateUI();
}

function fetchDevicesAndUpdateUI() {
  console.log('📡 Fetching from /devices...');
  fetch('/devices')
    .then(response => response.json())
    .then(devices => {
      console.log('✅ Devices fetched:', devices);
      updateTable(devices);
    })
    .catch(error => {
      console.error('❌ Error loading devices:', error);
    });
}

function updateTable(devices) {
    const tbody = document.getElementById('deviceTable').querySelector('tbody');
    tbody.innerHTML = '';
    devices.forEach((device, idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${idx + 1}</td>
                         <td>${device.name}</td>
                         <td>${device.ip || '-'}</td>
                         <td>${device.dns || 'N'}</td>
                         <td>${device.lastConnected || '-'}</td>`;
        tbody.appendChild(row);
    });
}

// Load devices on page load
window.onload = loadDevices;