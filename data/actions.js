function loadDevices() {
    fetch('/devices')
        .then(response => response.json())
        .then(devices => {
            const tbody = document.getElementById('deviceTable').querySelector('tbody');
            tbody.innerHTML = '';
            devices.forEach((device, idx) => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${idx + 1}</td>
                                 <td>${device.name}</td>
                                 <td>${device.ip}</td>
                                 <td>${device.dns}</td>
                                 <td>${device.lastConnected}</td>`;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading devices:', error);
        });
}

// instant updates via websocket
const ws = new WebSocket(`ws://${location.hostname}:81/`);
ws.onmessage = function(event) {
    if (event.data === "update") {
        loadDevices();
    }
};

window.onload = loadDevices;