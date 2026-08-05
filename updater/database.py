import json
import os
import psycopg
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


class Database:
    def __init__(self):
        self.conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        self.conn.autocommit = False

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def upsert_station(self, station):
        location = station["location"]

        with self.conn.cursor() as cur:

            cur.execute("""
                INSERT INTO stations (
                    node_id,
                    public_phone_number,
                    trading_name,
                    brand_name,
                    is_same_trading_and_brand_name,
                    temporary_closure,
                    permanent_closure,
                    permanent_closure_date,
                    is_motorway_service_station,
                    is_supermarket_service_station,
                    address_line_1,
                    address_line_2,
                    city,
                    county,
                    country,
                    postcode,
                    latitude,
                    longitude,
                    location,
                    raw_json
                )
                VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,
                    ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,
                    %s::jsonb
                )
                ON CONFLICT (node_id)
                DO UPDATE SET
                    public_phone_number = EXCLUDED.public_phone_number,
                    trading_name = EXCLUDED.trading_name,
                    brand_name = EXCLUDED.brand_name,
                    is_same_trading_and_brand_name = EXCLUDED.is_same_trading_and_brand_name,
                    temporary_closure = EXCLUDED.temporary_closure,
                    permanent_closure = EXCLUDED.permanent_closure,
                    permanent_closure_date = EXCLUDED.permanent_closure_date,
                    is_motorway_service_station = EXCLUDED.is_motorway_service_station,
                    is_supermarket_service_station = EXCLUDED.is_supermarket_service_station,
                    address_line_1 = EXCLUDED.address_line_1,
                    address_line_2 = EXCLUDED.address_line_2,
                    city = EXCLUDED.city,
                    county = EXCLUDED.county,
                    country = EXCLUDED.country,
                    postcode = EXCLUDED.postcode,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    location = EXCLUDED.location,
                    raw_json = EXCLUDED.raw_json,
                    last_synced = NOW()
            """, (
                station["node_id"],
                station["public_phone_number"],
                station["trading_name"],
                station["brand_name"],
                station["is_same_trading_and_brand_name"],
                station["temporary_closure"],
                station["permanent_closure"],
                station["permanent_closure_date"],
                station["is_motorway_service_station"],
                station["is_supermarket_service_station"],
                location["address_line_1"],
                location["address_line_2"],
                location["city"],
                location["county"],
                location["country"],
                location["postcode"],
                location["latitude"],
                location["longitude"],
                location["longitude"],
                location["latitude"],
                json.dumps(station)
            ))

            cur.execute(
                "DELETE FROM station_amenities WHERE node_id=%s",
                (station["node_id"],)
            )

            for amenity in station["amenities"]:
                cur.execute("""
                    INSERT INTO station_amenities
                    (node_id, amenity)
                    VALUES (%s,%s)
                """, (
                    station["node_id"],
                    amenity
                ))

            cur.execute(
                "DELETE FROM station_fuel_types WHERE node_id=%s",
                (station["node_id"],)
            )

            for fuel in station["fuel_types"]:
                cur.execute("""
                    INSERT INTO station_fuel_types
                    (node_id, fuel_type)
                    VALUES (%s,%s)
                """, (
                    station["node_id"],
                    fuel
                ))

            cur.execute(
                "DELETE FROM opening_hours WHERE node_id=%s",
                (station["node_id"],)
            )

            for day, hours in station["opening_times"]["usual_days"].items():

                cur.execute("""
                    INSERT INTO opening_hours
                    (
                        node_id,
                        day_name,
                        open_time,
                        close_time,
                        is_24_hours
                    )
                    VALUES (%s,%s,%s,%s,%s)
                """, (
                    station["node_id"],
                    day,
                    hours["open"],
                    hours["close"],
                    hours["is_24_hours"]
                ))

            bank = station["opening_times"]["bank_holiday"]

            cur.execute("""
                INSERT INTO opening_hours
                (
                    node_id,
                    day_name,
                    open_time,
                    close_time,
                    is_24_hours
                )
                VALUES (%s,%s,%s,%s,%s)
            """, (
                station["node_id"],
                "bank_holiday",
                bank["open_time"],
                bank["close_time"],
                bank["is_24_hours"]
            ))
    
    def upsert_prices(self, station_prices):
        node_id = station_prices["node_id"]

        with self.conn.cursor() as cur:
            for fuel in station_prices["fuel_prices"]:
                fuel_type = fuel["fuel_type"]
                price = fuel["price"]
                updated_at = fuel.get("price_change_effective_timestamp") or fuel.get("price_last_updated")

                if price is None:
                    continue

                # API returns strings like "0139.7000"
                # conv to decimal pounds/pence value
                price = float(price)

                # incase submitted pounds instead of pence
                if price < 3:
                    price *= 100

                # get current price
                cur.execute("""
                    SELECT price
                    FROM current_prices
                    WHERE node_id = %s
                    AND fuel_type = %s
                """, (
                    node_id,
                    fuel_type
                ))

                result = cur.fetchone()

                old_price = result[0] if result else None

                # only write history if price changed
                if old_price is None or float(old_price) != price:

                    cur.execute("""
                        INSERT INTO price_history
                        (
                            node_id,
                            fuel_type,
                            price,
                            changed_at
                        )
                        VALUES
                        (%s,%s,%s,%s)
                    """, (
                        node_id,
                        fuel_type,
                        price,
                        updated_at
                    ))

                    cur.execute("""
                        INSERT INTO current_prices
                        (
                            node_id,
                            fuel_type,
                            price,
                            updated_at
                        )
                        VALUES
                        (%s,%s,%s,%s)
                        ON CONFLICT(node_id, fuel_type)
                        DO UPDATE SET
                            price = EXCLUDED.price,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        node_id,
                        fuel_type,
                        price,
                        updated_at
                    ))

                else:
                    # price hasn't changed, keep the latest timestamp
                    cur.execute("""
                        UPDATE current_prices
                        SET updated_at = %s
                        WHERE node_id = %s
                        AND fuel_type = %s
                    """, (
                        updated_at,
                        node_id,
                        fuel_type
                    ))
    
    def get_sync_time(self, sync_name):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT last_sync
                FROM sync_state
                WHERE sync_name = %s
            """, (sync_name,))

            result = cur.fetchone()

            if result:
                return result[0]

            return None


    def update_sync_time(self, sync_name):
        now = datetime.now(timezone.utc)

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sync_state
                (
                    sync_name,
                    last_sync
                )
                VALUES
                (%s,%s)
                ON CONFLICT(sync_name)
                DO UPDATE SET
                    last_sync = EXCLUDED.last_sync
            """, (
                sync_name,
                now
            ))

    def database_initialised(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM stations
            """)

            count = cur.fetchone()[0]

            return count > 0

        self.commit()
        
    def acquire_lock(self, name):
        with self.conn.cursor() as cur:

            cur.execute("""
                INSERT INTO sync_lock
                (
                    lock_name,
                    locked,
                    locked_at
                )
                VALUES
                (%s, TRUE, NOW())
                ON CONFLICT(lock_name)
                DO UPDATE SET
                    locked = TRUE,
                    locked_at = NOW()
                WHERE sync_lock.locked = FALSE
                RETURNING locked
            """, (name,))

            result = cur.fetchone()

            self.commit()

            return result is not None


    def release_lock(self, name):
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE sync_lock
                SET locked = FALSE
                WHERE lock_name = %s
            """, (name,))

        self.commit()