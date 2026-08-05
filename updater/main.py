from database import Database
from fuel_api import FuelFinderAPI
from oauth import OAuthManager

oauth = OAuthManager()
api = FuelFinderAPI(oauth)
db = Database()

print("Downloading stations...")
stations = api.get_all_pages("/pfs")

print(f"Saving {len(stations)} stations")

for count, station in enumerate(stations, start=1):
    db.upsert_station(station)

    if count % 500 == 0:
        db.commit()
        print(f"Saved {count}/{len(stations)} stations")

db.commit()


print("Downloading prices...")
prices = api.get_all_pages("/pfs/fuel-prices")

print(f"Saving prices for {len(prices)} stations")

for count, station_prices in enumerate(prices, start=1):
    db.upsert_prices(station_prices)

    if count % 500 == 0:
        db.commit()
        print(f"Saved {count}/{len(prices)} price records")

db.commit()

db.close()