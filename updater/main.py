from updater.oauth import OAuthManager
from updater.fuel_api import FuelFinderAPI
from updater.database import Database
from updater.sync_manager import SyncManager

oauth = OAuthManager()

api = FuelFinderAPI(oauth)

db = Database()

sync = SyncManager(api, db)

sync.full_station_sync()
sync.full_price_sync()

db.close()