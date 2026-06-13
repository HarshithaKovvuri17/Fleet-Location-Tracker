# 🚚 Build a Fleet Location Tracker with PostGIS, PostgreSQL, and a Live Map UI

A production-ready **Real-Time Fleet Location Tracking System** built using **FastAPI, PostgreSQL, PostGIS, Docker, Server-Sent Events (SSE), and Leaflet.js**.

The system simulates vehicle movement, stores geospatial data in PostGIS, performs spatial analysis, detects geofence entry/exit events, and visualizes vehicle locations live on an interactive map.

---

## 📌 Project Overview

Fleet management companies need to monitor vehicle movement, track assets in real time, and generate alerts when vehicles enter or leave designated operational zones.

This project provides:

- ✅ Real-time vehicle tracking
- ✅ Live map visualization
- ✅ Geofence monitoring
- ✅ Spatial database operations using PostGIS
- ✅ Nearby vehicle discovery
- ✅ Event streaming using Server-Sent Events
- ✅ Dockerized deployment

---

## 🎯 Key Features

### Vehicle Tracking
- Tracks vehicle locations continuously
- Stores historical location data
- Simulates movement of multiple vehicles

### Geofence Management
- Create polygon-based geofences
- Detect vehicle entry events
- Detect vehicle exit events
- Generate real-time alerts

### Spatial Queries
- Find vehicles near depots
- Geospatial distance calculations
- Point-in-polygon detection
- K-Nearest Neighbor searches

### Real-Time Streaming
- Server-Sent Events (SSE)
- Live location updates
- Instant geofence notifications

### Interactive Map
- Leaflet.js integration
- Real-time marker updates
- Vehicle movement visualization
- Geofence display

---

## 🏗️ System Architecture

```text
┌─────────────────────┐
│ Vehicle Simulator   │
│ (Fleet Movement)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PostgreSQL +        │
│ PostGIS Database    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FastAPI Backend     │
│ REST APIs + SSE     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Leaflet Frontend    │
│ Live Map Dashboard  │
└─────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- Python
- FastAPI
- AsyncPG
- Psycopg2
- SSE-Starlette

### Database
- PostgreSQL 15
- PostGIS 3.3

### Frontend
- HTML5
- CSS3
- JavaScript
- Leaflet.js

### DevOps
- Docker
- Docker Compose

---

## 📂 Project Structure

```text
Fleet_Location_Tracker
│
├── backend
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── static
│       ├── index.html
│       ├── script.js
│       └── style.css
│
├── simulator
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── database
│   └── init.sql
│
├── docker-compose.yml
├── .env.example
├── submission.json
├── testing.md
└── README.md
```

---

## 🗄️ Database Design

### Vehicles

| Column | Type |
|----------|---------|
| id | SERIAL |
| license_plate | VARCHAR |
| type | VARCHAR |

### Depots

| Column | Type |
|----------|---------|
| id | SERIAL |
| name | VARCHAR |
| location | GEOMETRY(Point,4326) |

### Geofences

| Column | Type |
|----------|---------|
| id | SERIAL |
| name | VARCHAR |
| area | GEOMETRY(Polygon,4326) |

### Location Events

| Column | Type |
|----------|---------|
| id | BIGSERIAL |
| vehicle_id | INTEGER |
| timestamp | TIMESTAMPTZ |
| position | GEOMETRY(Point,4326) |
| speed_kmh | INTEGER |

---

## ⚡ Spatial Indexing

The system uses GIST indexes for high-performance geospatial queries.

```sql
CREATE INDEX idx_depots_location
ON depots USING GIST(location);

CREATE INDEX idx_geofences_area
ON geofences USING GIST(area);

CREATE INDEX idx_location_events_position
ON location_events USING GIST(position);
```

### Benefits
- Faster radius searches
- Efficient geofence checks
- Optimized nearest-neighbor lookups
- Scales to millions of records

---

## 🚀 Installation & Setup

### Prerequisites

Install:
- Docker
- Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

### Clone Repository

```bash
git clone https://github.com/yourusername/Fleet_Location_Tracker.git

cd Fleet_Location_Tracker
```

### Start Application

```bash
docker-compose up --build -d
```

### Verify Running Containers

```bash
docker ps
```

Expected services:

```text
db
api
simulator
```

---

## 🌐 Access Application

Open:

```text
http://localhost:8000
```

The live map dashboard will load automatically.

---

## 🔄 Real-Time Workflow

### Step 1
Simulator generates location updates.

### Step 2
Updates are stored in PostGIS.

### Step 3
FastAPI retrieves new records.

### Step 4
Geofence engine evaluates vehicle positions.

### Step 5
Events are pushed through SSE.

### Step 6
Leaflet map updates instantly.

---

## 📡 Geofence Detection Logic

```python
if is_inside and not was_inside:
    generate_entry_event()

elif not is_inside and was_inside:
    generate_exit_event()
```

### Sample Entry Event

```json
{
  "type": "geofence_entry",
  "vehicle_id": 12,
  "geofence_id": 1
}
```

### Sample Exit Event

```json
{
  "type": "geofence_exit",
  "vehicle_id": 12,
  "geofence_id": 1
}
```

---

## 📈 Performance Optimizations

### Batch Inserts

The simulator uses bulk inserts rather than inserting records one by one.

```python
execute_values()
```

### Advantages

- Reduced database round trips
- Faster ingestion
- Lower transaction overhead
- Better scalability

---

## 🔒 Production Features

- ✅ Dockerized deployment
- ✅ Environment variable configuration
- ✅ Spatial indexing
- ✅ Real-time event streaming
- ✅ Geofence state tracking
- ✅ Asynchronous FastAPI services
- ✅ PostGIS geospatial support

---

## 🧪 Testing

### Start Services

```bash
docker-compose up
```

### Check API Documentation

```text
http://localhost:8000/docs
```

### Open Dashboard

```text
http://localhost:8000
```

### View Simulator Logs

```bash
docker logs <simulator-container>
```

Expected output:

```text
Inserted location events successfully
```

---

## 📊 Future Enhancements

- Route optimization
- Driver behavior analytics
- Fuel consumption monitoring
- Historical trip playback
- User authentication & authorization
- Kafka event streaming
- Redis caching
- Mobile application
- WebSocket support
- AWS/Azure/GCP deployment

---

## 👨‍💻 Author

**Kovvuri Harshitha**
- Email: harshitahanisha@gmail.com
- Github Url: "https://github.com/HarshithaKovvuri17/Fleet-Location-Tracker.git"

---

## ⭐ Project Highlights

- Real-Time Fleet Monitoring
- FastAPI Backend
- PostgreSQL + PostGIS
- Dockerized Deployment
- Server-Sent Events (SSE)
- Live Vehicle Tracking Dashboard
- Geofence Entry/Exit Detection
- Spatial Query Optimization
- Production-Ready Architecture

---
