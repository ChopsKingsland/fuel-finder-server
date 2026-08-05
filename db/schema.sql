CREATE EXTENSION IF NOT EXISTS postgis;

-- stations

CREATE TABLE stations (
    node_id TEXT PRIMARY KEY,
    public_phone_number TEXT,
    trading_name TEXT NOT NULL,
    brand_name TEXT NOT NULL,
    is_same_trading_and_brand_name BOOLEAN NOT NULL,
    temporary_closure BOOLEAN NOT NULL,
    permanent_closure BOOLEAN NOT NULL,
    permanent_closure_date DATE,
    is_motorway_service_station BOOLEAN NOT NULL,
    is_supermarket_service_station BOOLEAN NOT NULL,
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    county TEXT,
    country TEXT,
    postcode TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    location GEOGRAPHY(POINT,4326) NOT NULL,
    raw_json JSONB NOT NULL,
    last_synced TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_station_location
ON stations
USING GIST (location);

CREATE INDEX idx_station_brand
ON stations (brand_name);

CREATE INDEX idx_station_postcode
ON stations (postcode);

CREATE INDEX idx_station_city
ON stations (city);



-- amenities

CREATE TABLE station_amenities (
    node_id TEXT NOT NULL
        REFERENCES stations(node_id)
        ON DELETE CASCADE,
    amenity TEXT NOT NULL,
    PRIMARY KEY (node_id, amenity)
);

CREATE INDEX idx_station_amenity
ON station_amenities (amenity);

-- furl types available

CREATE TABLE station_fuel_types (

    node_id TEXT NOT NULL
        REFERENCES stations(node_id)
        ON DELETE CASCADE,
    fuel_type TEXT NOT NULL,
    PRIMARY KEY (node_id, fuel_type)
);

CREATE INDEX idx_station_fuel_type
ON station_fuel_types (fuel_type);


-- opening hours

CREATE TABLE opening_hours (

    node_id TEXT NOT NULL
        REFERENCES stations(node_id)
        ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    open_time TIME,
    close_time TIME,
    is_24_hours BOOLEAN NOT NULL,
    PRIMARY KEY (node_id, day_name)
);


-- current prices

CREATE TABLE current_prices (
    node_id TEXT NOT NULL
        REFERENCES stations(node_id)
        ON DELETE CASCADE,
    fuel_type TEXT NOT NULL,
    price NUMERIC(6,4),
    updated_at TIMESTAMPTZ,
    PRIMARY KEY (node_id, fuel_type)
);

CREATE INDEX idx_current_prices_fuel
ON current_prices (fuel_type);

CREATE INDEX idx_current_prices_price
ON current_prices (price);

-- price history

CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    node_id TEXT NOT NULL
        REFERENCES stations(node_id)
        ON DELETE CASCADE,
    fuel_type TEXT NOT NULL,
    price NUMERIC(6,4) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_price_history_station
ON price_history (node_id);

CREATE INDEX idx_price_history_date
ON price_history (changed_at);


-- sync state + runs

CREATE TABLE sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE sync_runs (
    id BIGSERIAL PRIMARY KEY,
    sync_type TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    success BOOLEAN,
    records_processed INTEGER,
    error_message TEXT
);