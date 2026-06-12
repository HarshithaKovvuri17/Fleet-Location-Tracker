# Fleet Location Tracker Testing Guide

This guide provides the exact commands you need to run to verify each core requirement of the project and ensure you receive full marks during evaluation.

## Requirement 1: Docker Initialization
**Goal:** Verify all services start and database is seeded.
```bash
# 1. Start the services
docker compose up --build -d

# 2. Wait ~30 seconds, then check if all services are 'Up' and db is 'healthy'
docker compose ps
```
> **Note:** If you ever need to reset the database and start completely fresh, run:
> `docker compose down -v` (this will automatically remove the named `pgdata` volume).

## Requirement 2 & 3: Database & Simulator Verification
**Goal:** Verify the correct schema, GIST indexes, and that the simulator is inserting data for 50 vehicles.
```bash
# 1. Access the PostgreSQL database
docker exec -it fleet_location_tracker-db-1 psql -U postgres -d fleet_tracker

# 2. Inside psql, verify the tables and indexes exist:
\d location_events
\di

# 3. Verify simulator has created 50 distinct vehicles:
SELECT COUNT(DISTINCT vehicle_id) FROM location_events;

# 4. Run this query twice separated by 10 seconds. The total count should increase.
SELECT COUNT(*) FROM location_events;

# 5. Exit psql
\q
```

## Requirement 4: Proximity API
**Goal:** Find vehicles within a specified radius using `ST_DWithin`.
```bash
# Verify vehicles within 1000 meters of the test depot coordinates (-74.00, 40.71)
curl "http://localhost:8000/api/vehicles/proximity?lat=40.71&lon=-74.00&radius_meters=1000"
```
*You should see a JSON array of vehicle objects that are near the specified point.*

## Requirement 5: Nearest Vehicles API
**Goal:** Find the N nearest vehicles using the `<->` distance operator.
```bash
# Find the 5 nearest vehicles to the coordinates
curl "http://localhost:8000/api/vehicles/nearest?lat=40.71&lon=-74.00&limit=5"
```
*You should see exactly 5 vehicles returned, sorted by `distance_meters` in ascending order.*

## Requirement 6: Geofence Events API
**Goal:** Check which vehicles have entered or exited a geofence recently.
```bash
# Check events for Geofence ID 1 over the last 10 minutes
curl "http://localhost:8000/api/geofences/1/events?minutes=10"
```
*You should see a JSON object containing an `entries` array and an `exits` array populated with timestamps.*

## Requirement 7: Real-Time SSE Endpoint
**Goal:** Verify the server pushes live geofence entry/exit alerts.

**Windows (PowerShell / Command Prompt):**
```powershell
# Windows has curl.exe built-in. Use -N to disable buffering:
curl.exe -N http://localhost:8000/api/events
```
*(Alternative legacy PowerShell script):*
```powershell
$request = [System.Net.WebRequest]::Create("http://localhost:8000/api/events")
$response = $request.GetResponse()
$stream = $response.GetResponseStream()
$reader = New-Object System.IO.StreamReader($stream)
while ($true) {
    $line = $reader.ReadLine()
    if ($line) { Write-Host $line }
}
```

**Linux/macOS (bash):**
```bash
curl -N http://localhost:8000/api/events
```

*You will see raw data streams containing `event: location_update`, `event: geofence_entry`, and `event: geofence_exit` payloads.*

## Requirement 8 & 9: Frontend Live Map
**Goal:** Verify the Leaflet UI loads and responds to SSE data.
1. Open your web browser and go to `http://localhost:8000/` (it will directly serve the live map at root).
2. Look at the page elements to verify:
   - A map of NYC with blue vehicle marker pins.
   - A **"Fleet Status"** sidebar on the left.
   - A blue geofence polygon drawn on Manhattan.
3. Open browser Developer Tools (`Ctrl+Shift+I` or right-click and select **Inspect Element**):
   - Go to the **Console** tab and verify the message `Loaded 50 vehicles.` is printed.
   - Go to the **Elements** tab, press `Ctrl+F` (or `Cmd+F` on macOS) and search for the following target attributes:
     - Search for `data-testid="map-container"`
     - Search for `data-testid="geofence-polygon-1"`
     - Search for `data-testid="vehicle-marker-` (e.g. `data-testid="vehicle-marker-1"`, `data-testid="vehicle-marker-2"`, etc.)
4. Observe the live simulation behavior:
   - Vehicle markers should move dynamically on the map.
   - When a vehicle enters or exits the geofence boundary:
     - A log entry (e.g. `1:30:00 pm - Vehicle 27 ENTERED geofence 1`) will be prepended to the **"Fleet Status"** sidebar.
     - The geofence polygon on the map will flash red for 3 seconds (verifiable in the inspector by checking if the class `alert-active` is temporarily added to the geofence polygon's path element).

## Requirement 10 & 11: Configuration Files
**Goal:** Verify required configuration and submission files exist.
```bash
# These files should exist in the root of your project directory
cat .env.example
cat submission.json
```
