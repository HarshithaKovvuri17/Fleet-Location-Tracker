const map = L.map('map-container').setView([40.7128, -74.0060], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

const vehicleMarkers = {};
const geofenceLayers = {};

fetch('/api/geofences')
    .then(res => res.json())
    .then(geofences => {
        geofences.forEach(gf => {
            const layer = L.geoJSON(gf.area, {
                style: {
                    color: 'blue',
                    weight: 2,
                    fillOpacity: 0.2
                }
            }).addTo(map);
            
            layer.eachLayer(function(l) {
                const setGeofenceTestId = () => {
                    const el = l.getElement() || l._path;
                    if (el) {
                        el.setAttribute('data-testid', `geofence-polygon-${gf.id}`);
                        geofenceLayers[gf.id] = el;
                        console.log(`Successfully set data-testid="geofence-polygon-${gf.id}"`);
                    }
                };

                const el = l.getElement() || l._path;
                if (el) {
                    setGeofenceTestId();
                } else {
                    l.on('add', setGeofenceTestId);
                }
            });
            
            layer.bindPopup(gf.name);
        });
    });

fetch('/api/vehicles')
    .then(res => res.json())
    .then(vehicles => {
        console.log(`Loaded ${vehicles.length} vehicles.`);
    });

const eventSource = new EventSource('/api/events');

eventSource.addEventListener('location_update', (event) => {
    const data = JSON.parse(event.data);
    const vid = data.vehicle_id;
    const lat = data.lat;
    const lon = data.lon;
    
    if (vehicleMarkers[vid]) {
        vehicleMarkers[vid].setLatLng([lat, lon]);
    } else {
        const marker = L.marker([lat, lon]).addTo(map);
        
        const setMarkerTestId = () => {
            const el = marker.getElement() || marker._icon;
            if (el) {
                el.setAttribute('data-testid', `vehicle-marker-${vid}`);
                console.log(`Successfully set data-testid="vehicle-marker-${vid}"`);
            }
        };

        const el = marker.getElement() || marker._icon;
        if (el) {
            setMarkerTestId();
        } else {
            marker.on('add', setMarkerTestId);
        }

        marker.bindPopup(`Vehicle ${vid}`);
        vehicleMarkers[vid] = marker;
    }
});

eventSource.addEventListener('geofence_entry', (event) => {
    const data = JSON.parse(event.data);
    showAlert(`Vehicle ${data.vehicle_id} ENTERED geofence ${data.geofence_id}`, 'entry');
    triggerGeofenceAlert(data.geofence_id);
});

eventSource.addEventListener('geofence_exit', (event) => {
    const data = JSON.parse(event.data);
    showAlert(`Vehicle ${data.vehicle_id} EXITED geofence ${data.geofence_id}`, 'exit');
    triggerGeofenceAlert(data.geofence_id);
});

function showAlert(message, type) {
    const alertsDiv = document.getElementById('alerts');
    const div = document.createElement('div');
    div.className = `alert-box ${type}`;
    div.innerText = `${new Date().toLocaleTimeString()} - ${message}`;
    alertsDiv.prepend(div);
}

function triggerGeofenceAlert(geofenceId) {
    const pathElem = geofenceLayers[geofenceId];
    if (pathElem) {
        // SVG paths classList support
        let currentClass = pathElem.getAttribute('class') || '';
        if (!currentClass.includes('alert-active')) {
            pathElem.setAttribute('class', currentClass + ' alert-active');
        }
        
        setTimeout(() => {
            let updatedClass = pathElem.getAttribute('class') || '';
            pathElem.setAttribute('class', updatedClass.replace('alert-active', '').trim());
        }, 3000);
    }
}
