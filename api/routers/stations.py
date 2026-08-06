from fastapi import APIRouter, Depends, Query
from psycopg import Connection
from psycopg.rows import dict_row
from api.database import get_db

router = APIRouter(prefix="/stations", tags=["Stations"])

@router.get("/nearby")
def get_nearby_stations(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    radius_miles: float = Query(10.0, description="Search radius in miles"),
    db: Connection = Depends(get_db)
):
    # Convert miles to metres for PostGIS
    radius_metres = radius_miles * 1609.344
    
    query = """
        SELECT 
            s.*,
            COALESCE(cp.prices, '{}'::jsonb) AS prices,
            COALESCE(a.amenities, '[]'::jsonb) AS amenities,
            COALESCE(oh.hours, '[]'::jsonb) AS opening_hours,
            ST_Distance(s.location, ST_MakePoint(%(lon)s, %(lat)s)::geography) * 0.000621371 AS distance_miles
        FROM stations s
        LEFT JOIN LATERAL (
            SELECT jsonb_object_agg(
                fuel_type, 
                jsonb_build_object('price', price, 'updated_at', updated_at)
            ) AS prices
            FROM current_prices
            WHERE node_id = s.node_id
        ) cp ON true
        LEFT JOIN LATERAL (
            SELECT jsonb_agg(amenity) AS amenities
            FROM station_amenities
            WHERE node_id = s.node_id
        ) a ON true
        LEFT JOIN LATERAL (
            SELECT jsonb_agg(jsonb_build_object(
                'day', day_name, 
                'open_time', open_time, 
                'close_time', close_time, 
                'is_24_hours', is_24_hours
            )) AS hours
            FROM opening_hours
            WHERE node_id = s.node_id
        ) oh ON true
        WHERE ST_DWithin(
            s.location, 
            ST_MakePoint(%(lon)s, %(lat)s)::geography, 
            %(radius_metres)s
        )
        AND cp.prices IS NOT NULL
        ORDER BY distance_miles, s.node_id;
    """
    
    with db.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, {
            "lon": lon,
            "lat": lat,
            "radius_metres": radius_metres
        })
        results = cursor.fetchall()
        
        # Remove raw PostgreSQL binary/internal fields before returning
        for row in results:
            row.pop('location', None)
            row.pop('raw_json', None)
            
        return {"stations": results}

@router.get("/{node_id}/history")
def get_station_history(
    node_id: str,
    db: Connection = Depends(get_db)
):
    query = """
        SELECT 
            fuel_type, 
            price, 
            changed_at
        FROM price_history
        WHERE node_id = %(node_id)s
        ORDER BY changed_at DESC
    """
    
    with db.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, {"node_id": node_id})
        results = cursor.fetchall()
        
        return {"history": results}
