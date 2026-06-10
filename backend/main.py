import asyncio
import json
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fleet_tracker")

db_pool = None
vehicle_geofence_state = {}
sse_queue = asyncio.Queue()

async def location_poller():
    """Polls database for the latest location of all vehicles to broadcast to frontend."""
    last_check = datetime.now(timezone.utc)
    while True:
        await asyncio.sleep(2)
        if not db_pool:
            continue
            
        try:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT vehicle_id, ST_X(position) as lon, ST_Y(position) as lat, timestamp 
                    FROM location_events 
                    WHERE timestamp > $1
                    ORDER BY timestamp ASC
                """
                rows = await conn.fetch(query, last_check)
                if rows:
                    last_check = max([r["timestamp"] for r in rows])
                    for r in rows:
                        await sse_queue.put({
                            "type": "location_update",
                            "data": {
                                "vehicle_id": r["vehicle_id"],
                                "lat": r["lat"],
                                "lon": r["lon"],
                                "timestamp": r["timestamp"].isoformat()
                            }
                        })
        except Exception as e:
            print(f"Error in location_poller: {e}")

async def alert_engine():
    """Polls database to detect geofence entries/exits."""
    while True:
        await asyncio.sleep(5)
        if not db_pool:
            continue
            
        try:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT v.id as vehicle_id, g.id as geofence_id, 
                           ST_Contains(g.area, le.position) as is_inside
                    FROM vehicles v
                    JOIN (
                        SELECT vehicle_id, MAX(timestamp) as latest_timestamp
                        FROM location_events
                        GROUP BY vehicle_id
                    ) latest_events ON v.id = latest_events.vehicle_id
                    JOIN location_events le ON le.vehicle_id = v.id AND le.timestamp = latest_events.latest_timestamp
                    CROSS JOIN geofences g
                """
                rows = await conn.fetch(query)
                
                for r in rows:
                    v_id = r["vehicle_id"]
                    g_id = r["geofence_id"]
                    is_inside = r["is_inside"]
                    
                    state_key = (v_id, g_id)
                    was_inside = vehicle_geofence_state.get(state_key, False)
                    
                    if is_inside and not was_inside:
                        vehicle_geofence_state[state_key] = True
                        await sse_queue.put({
                            "type": "geofence_entry",
                            "data": {
                                "vehicle_id": v_id,
                                "geofence_id": g_id,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        })
                    elif not is_inside and was_inside:
                        vehicle_geofence_state[state_key] = False
                        await sse_queue.put({
                            "type": "geofence_exit",
                            "data": {
                                "vehicle_id": v_id,
                                "geofence_id": g_id,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        })
        except Exception as e:
            print(f"Error in alert_engine: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    while True:
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL)
            print("Connected to database")
            break
        except Exception as e:
            print(f"Failed to connect to db, retrying in 2s... {e}")
            await asyncio.sleep(2)
            
    alert_task = asyncio.create_task(alert_engine())
    location_poll_task = asyncio.create_task(location_poller())
    
    yield
    
    alert_task.cancel()
    location_poll_task.cancel()
    if db_pool:
        await db_pool.close()

app = FastAPI(lifespan=lifespan)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/vehicles")
async def get_vehicles():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, license_plate FROM vehicles")
        return [{"id": r["id"], "license_plate": r["license_plate"]} for r in rows]

@app.get("/api/geofences")
async def get_geofences():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, ST_AsGeoJSON(area) as area_json FROM geofences")
        res = []
        for r in rows:
            res.append({
                "id": r["id"],
                "name": r["name"],
                "area": json.loads(r["area_json"])
            })
        return res

@app.get("/api/vehicles/proximity")
async def vehicles_proximity(lat: float, lon: float, radius_meters: int):
    query = """
        SELECT v.id, v.license_plate
        FROM vehicles v
        JOIN (
            SELECT vehicle_id, MAX(timestamp) as latest_timestamp
            FROM location_events
            GROUP BY vehicle_id
        ) latest_events ON v.id = latest_events.vehicle_id
        JOIN location_events le ON le.vehicle_id = v.id AND le.timestamp = latest_events.latest_timestamp
        WHERE ST_DWithin(le.position::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, lon, lat, radius_meters)
        return [{"id": r["id"], "license_plate": r["license_plate"]} for r in rows]

@app.get("/api/vehicles/nearest")
async def vehicles_nearest(lat: float, lon: float, limit: int = 5):
    query = """
        SELECT v.id, v.license_plate, 
               ST_Distance(le.position::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) as distance_meters
        FROM vehicles v
        JOIN (
            SELECT vehicle_id, MAX(timestamp) as latest_timestamp
            FROM location_events
            GROUP BY vehicle_id
        ) latest_events ON v.id = latest_events.vehicle_id
        JOIN location_events le ON le.vehicle_id = v.id AND le.timestamp = latest_events.latest_timestamp
        ORDER BY le.position <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)
        LIMIT $3
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, lon, lat, limit)
        return [{"id": r["id"], "license_plate": r["license_plate"], "distance_meters": r["distance_meters"]} for r in rows]

@app.get("/api/geofences/{geofence_id}/events")
async def geofence_events(geofence_id: int, minutes: int = 10):
    query = """
        WITH geofence AS (
            SELECT area FROM geofences WHERE id = $1
        ),
        vehicle_events AS (
            SELECT 
                vehicle_id, 
                timestamp,
                position,
                LAG(position) OVER (PARTITION BY vehicle_id ORDER BY timestamp) as prev_position
            FROM location_events
            WHERE timestamp >= NOW() - INTERVAL '1 minute' * $2
        )
        SELECT vehicle_id, timestamp, 
               CASE 
                   WHEN ST_Contains((SELECT area FROM geofence), position) AND NOT ST_Contains((SELECT area FROM geofence), prev_position) THEN 'entry'
                   WHEN NOT ST_Contains((SELECT area FROM geofence), position) AND ST_Contains((SELECT area FROM geofence), prev_position) THEN 'exit'
               END as event_type
        FROM vehicle_events
        WHERE prev_position IS NOT NULL
          AND (
              (ST_Contains((SELECT area FROM geofence), position) AND NOT ST_Contains((SELECT area FROM geofence), prev_position))
              OR 
              (NOT ST_Contains((SELECT area FROM geofence), position) AND ST_Contains((SELECT area FROM geofence), prev_position))
          )
        ORDER BY timestamp DESC
    """
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, geofence_id, minutes)
        entries = []
        exits = []
        for r in rows:
            evt = {"vehicle_id": r["vehicle_id"], "timestamp": r["timestamp"].isoformat(), "event_type": r["event_type"]}
            if r["event_type"] == 'entry':
                entries.append(evt)
            elif r["event_type"] == 'exit':
                exits.append(evt)
        
        return {"entries": entries, "exits": exits}

@app.get("/api/events")
async def sse_events():
    async def event_generator():
        while True:
            event = await sse_queue.get()
            yield {
                "event": event["type"],
                "data": json.dumps(event["data"])
            }
    
    return EventSourceResponse(event_generator())
