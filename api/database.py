import os
from psycopg_pool import ConnectionPool

# Build connection string from individual POSTGRES environment variables
host = os.environ.get("POSTGRES_HOST", "localhost")
port = os.environ.get("POSTGRES_PORT", "5432")
dbname = os.environ.get("POSTGRES_DB", "fuel_finder")
user = os.environ.get("POSTGRES_USER", "fuel")
password = os.environ.get("POSTGRES_PASSWORD", "password")

conninfo = f"host={host} port={port} dbname={dbname} user={user} password={password}"

pool = ConnectionPool(
    conninfo=conninfo,
    open=False, # We will open it explicitly on startup
    min_size=2,
    max_size=10
)

def get_db():
    """Dependency to get a database connection from the pool."""
    with pool.connection() as conn:
        yield conn
