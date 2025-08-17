"""Optimized SQL queries for postal code operations."""

import sqlite3
import math
from typing import List, Optional, Dict, Any
from .connection import DatabaseConnection
from .models import PostalCodeRecord, PostalSearchInput, ReverseGeocodeInput, row_to_postal_record


class PostalQueries:
    """High-performance postal code query operations."""
    
    def __init__(self) -> None:
        self.db_conn = DatabaseConnection()
    
    def find_by_postal_code(self, postal_code: str) -> Optional[PostalCodeRecord]:
        """Find exact postal code match."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm, 'US' as country_code, city
            FROM postal_codes 
            WHERE zcta_code = ?
        """
        
        cursor.execute(query, (postal_code,))
        row = cursor.fetchone()
        
        if row:
            return row_to_postal_record(row)
        return None
    
    def find_by_prefix(self, prefix: str, limit: int = 10) -> List[PostalCodeRecord]:
        """Find postal codes starting with prefix."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm, 'US' as country_code, city
            FROM postal_codes 
            WHERE zcta_code LIKE ? || '%'
            ORDER BY zcta_code
            LIMIT ?
        """
        
        cursor.execute(query, (prefix, limit))
        rows = cursor.fetchall()
        
        return [row_to_postal_record(row) for row in rows]
    
    def search(self, params: PostalSearchInput) -> List[PostalCodeRecord]:
        """Advanced search with multiple criteria."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm, 'US' as country_code, city
            FROM postal_codes 
            WHERE 1=1
        """
        
        query_params: List[Any] = []
        
        if params.postalcode:
            query += " AND zcta_code = ?"
            query_params.append(params.postalcode)
        elif params.postalcode_startsWith:
            query += " AND zcta_code LIKE ? || '%'"
            query_params.append(params.postalcode_startsWith)
        
        query += " ORDER BY zcta_code LIMIT ?"
        query_params.append(params.maxRows)
        
        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        
        return [row_to_postal_record(row) for row in rows]
    
    def find_near_coordinates(
        self, 
        params: ReverseGeocodeInput
    ) -> List[Dict[str, Any]]:
        """Find postal codes near coordinates with distance calculation."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        lat, lng, radius, max_results = params.latitude, params.longitude, params.radius, params.maxResults
        
        # Calculate bounding box for performance optimization
        lat_range = radius / 111.32  # roughly 1 degree latitude = 111.32 km
        lng_range = radius / (111.32 * math.cos(math.radians(lat)))
        
        min_lat = lat - lat_range
        max_lat = lat + lat_range
        min_lng = lng - lng_range
        max_lng = lng + lng_range
        
        query = """
            SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm, 'US' as country_code, city,
                   SQRT(
                       (latitude - ?) * (latitude - ?) + 
                       (longitude - ?) * (longitude - ?)
                   ) * 111.32 as distance
            FROM postal_codes 
            WHERE latitude BETWEEN ? AND ? 
              AND longitude BETWEEN ? AND ?
              AND SQRT(
                  (latitude - ?) * (latitude - ?) + 
                  (longitude - ?) * (longitude - ?)
              ) * 111.32 <= ?
            ORDER BY distance 
            LIMIT ?
        """
        
        query_params = [
            lat, lat, lng, lng,  # distance calculation
            min_lat, max_lat, min_lng, max_lng,  # bounding box
            lat, lat, lng, lng,  # distance filter
            radius,
            max_results
        ]
        
        cursor.execute(query, query_params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            record_dict = dict(row)
            results.append(record_dict)
        
        return results
    
    def validate_postal_code(self, postal_code: str) -> bool:
        """Check if postal code exists in database."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT 1 FROM postal_codes WHERE zcta_code = ? LIMIT 1"
        cursor.execute(query, (postal_code,))
        
        return cursor.fetchone() is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) as count FROM postal_codes")
        total_records = cursor.fetchone()['count']
        
        # Unique states
        cursor.execute("SELECT COUNT(DISTINCT state) as count FROM postal_codes")
        unique_states = cursor.fetchone()['count']
        
        # Database file size (approximate)
        try:
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()['size']
        except:
            db_size = 0
        
        return {
            "totalRecords": total_records,
            "uniqueStates": unique_states,
            "databaseSize": db_size,
            "status": "connected"
        }