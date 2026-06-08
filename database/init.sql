CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    license_plate VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) DEFAULT 'Van'
);

CREATE TABLE depots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL
);

CREATE TABLE geofences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    area GEOMETRY(Polygon, 4326) NOT NULL
);

CREATE TABLE location_events (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(id),
    timestamp TIMESTAMPTZ NOT NULL,
    position GEOMETRY(Point, 4326) NOT NULL,
    speed_kmh INTEGER
);

-- GIST Indexes
CREATE INDEX idx_depots_location ON depots USING GIST (location);
CREATE INDEX idx_geofences_area ON geofences USING GIST (area);
CREATE INDEX idx_location_events_position ON location_events USING GIST (position);

-- Seed Data from submission.json
INSERT INTO vehicles (id, license_plate) VALUES (1, 'TEST-123');

INSERT INTO depots (id, name, location) VALUES 
(1, 'Test Depot', ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326));

INSERT INTO geofences (id, name, area) VALUES 
(1, 'Test Geofence', ST_SetSRID(ST_GeomFromText('POLYGON((-74.01 40.71, -74.00 40.71, -74.00 40.72, -74.01 40.72, -74.01 40.71))'), 4326));

-- Ensure sequences are updated to avoid ID conflicts later
SELECT setval('vehicles_id_seq', (SELECT MAX(id) FROM vehicles));
SELECT setval('depots_id_seq', (SELECT MAX(id) FROM depots));
SELECT setval('geofences_id_seq', (SELECT MAX(id) FROM geofences));
