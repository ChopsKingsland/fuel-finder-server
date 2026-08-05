from apscheduler.schedulers.blocking import BlockingScheduler
from updater.oauth import OAuthManager
from updater.fuel_api import FuelFinderAPI
from updater.database import Database
from updater.sync_manager import SyncManager


oauth = OAuthManager()
api = FuelFinderAPI(oauth)
db = Database()

sync = SyncManager(api, db)


def update_prices():
    print("Starting price update")

    if not db.acquire_lock("price_update"):
        print("Price update already running")
        return

    try:
        sync.incremental_price_sync()

    finally:
        db.release_lock("price_update")


def update_stations():
    print("Starting station update")

    if not db.acquire_lock("station_update"):
        print("Station update already running")
        return

    try:
        sync.incremental_price_sync()

    finally:
        db.release_lock("station_update")


def weekly_full_sync():
    print("Starting weekly full sync")
    try:
        sync.full_station_sync()
        sync.full_price_sync()
        print("Weekly sync complete")
    except Exception as e:
        db.rollback()
        print(f"Weekly sync failed: {e}")

def initial_sync():
    print("Checking database state...")

    if not db.database_initialised():
        print("Database empty, running initial sync")

        sync.full_station_sync()
        sync.full_price_sync()

        print("Initial sync complete")

    else:
        print("Database already populated")

scheduler = BlockingScheduler()


# prices every 30 minutes
scheduler.add_job(
    update_prices,
    "interval",
    minutes=30
)


# stations every 24 hours
scheduler.add_job(
    update_stations,
    "interval",
    hours=24
)


# full rebuild every Sunday at 03:00
scheduler.add_job(
    weekly_full_sync,
    "cron",
    day_of_week="sun",
    hour=3,
    minute=0
)


print("Fuel Finder updater running")


initial_sync()
scheduler.start()