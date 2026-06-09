import os
import time
import random
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fleet_tracker")

def get_connection():
    while True:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("Connected to database")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Waiting for database... {e}")
            time.sleep(2)

def main():
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    # Ensure 50 vehicles
    cursor.execute("SELECT id FROM vehicles")
    existing_vehicles = [row[0] for row in cursor.fetchall()]
    
    needed_vehicles = 50 - len(existing_vehicles)
    if needed_vehicles > 0:
        print(f"Creating {needed_vehicles} vehicles...")
        new_vehicles = [(f"SIM-{i}-{random.randint(1000, 9999)}", "Van") for i in range(needed_vehicles)]
        execute_values(
            cursor,
            "INSERT INTO vehicles (license_plate, type) VALUES %s ON CONFLICT DO NOTHING",
            new_vehicles
        )
    
    cursor.execute("SELECT id FROM vehicles")
    vehicle_ids = [row[0] for row in cursor.fetchall()]
    
    # Initialize positions around NYC: 40.7128, -74.0060
    # Also near the test geofence: -74.00 to -74.01, 40.71 to 40.72
    base_lat = 40.7128
    base_lon = -74.0060
    
    positions = {vid: (base_lon + random.uniform(-0.02, 0.02), base_lat + random.uniform(-0.02, 0.02)) for vid in vehicle_ids}
    
    print("Starting simulation loop...")
    while True:
        start_time = time.time()
        
        events = []
        now = datetime.now(timezone.utc)
        
        for vid in vehicle_ids:
            lon, lat = positions[vid]
            # Move slowly
            lon += random.uniform(-0.001, 0.001)
            lat += random.uniform(-0.001, 0.001)
            positions[vid] = (lon, lat)
            
            speed = random.randint(0, 60)
            events.append((vid, now, f"SRID=4326;POINT({lon} {lat})", speed))
        
        insert_query = """
            INSERT INTO location_events (vehicle_id, timestamp, position, speed_kmh) 
            VALUES %s
        """
        execute_values(cursor, insert_query, events)
        print(f"Inserted {len(events)} location events at {now}")
        
        elapsed = time.time() - start_time
        sleep_time = max(0, 5.0 - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
