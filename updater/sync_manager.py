from datetime import datetime, timezone


class SyncManager:

    def __init__(self, api, db):
        self.api = api
        self.db = db

    def full_station_sync(self):
        print("Downloading all stations...")

        stations = self.api.get_all_pages("/pfs")

        print(f"Saving {len(stations)} stations")

        for count, station in enumerate(stations, start=1):
            self.db.upsert_station(station)

            if count % 500 == 0:
                self.db.commit()
                print(f"Saved {count}/{len(stations)} stations")

        self.db.commit()
        self.db.update_sync_time("station_sync")

        print("Station sync complete")


    def full_price_sync(self):
        print("Downloading all prices...")

        prices = self.api.get_all_pages("/pfs/fuel-prices")

        print(f"Saving prices for {len(prices)} stations")

        for count, station_prices in enumerate(prices, start=1):
            self.db.upsert_prices(station_prices)

            if count % 500 == 0:
                self.db.commit()
                print(f"Saved {count}/{len(prices)} price records")

        self.db.commit()
        self.db.update_sync_time("price_sync")

        print("Price sync complete")


    def incremental_station_sync(self):
        last_sync = self.db.get_sync_time("station_sync")

        if last_sync is None:
            return self.full_station_sync()

        timestamp = last_sync.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Updating stations since {timestamp}")

        params = {
            "effective-start-timestamp": timestamp
        }

        stations = self.api.get_all_pages(
            "/pfs",
            params=params
        )

        print(f"Updating {len(stations)} stations")

        for station in stations:
            self.db.upsert_station(station)

        self.db.commit()
        self.db.update_sync_time("station_sync")


    def incremental_price_sync(self):
        last_sync = self.db.get_sync_time("price_sync")

        if last_sync is None:
            return self.full_price_sync()

        timestamp = last_sync.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Updating prices since {timestamp}")

        params = {
            "effective-start-timestamp": timestamp
        }

        prices = self.api.get_all_pages(
            "/pfs/fuel-prices",
            params=params
        )

        print(f"Updating prices for {len(prices)} stations")

        for station_prices in prices:
            self.db.upsert_prices(station_prices)

        self.db.commit()
        self.db.update_sync_time("price_sync")