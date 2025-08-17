"""MCP server implementation for postal code geocoding using FastMCP."""

import sys
import os
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Debug: Print environment info
print(f"DEBUG: Python executable: {sys.executable}")
print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: __file__: {__file__}")
print(f"DEBUG: sys.path: {sys.path}")

# Handle imports for both installed package and direct execution
try:
    # Try absolute imports first (when package is installed)
    print("DEBUG: Attempting absolute imports...")
    from mcp_postal_geocoder.server.database.connection import DatabaseConnection
    from mcp_postal_geocoder.server.database.queries import PostalQueries
    from mcp_postal_geocoder.server.database.models import PostalSearchInput, ReverseGeocodeInput
    print("DEBUG: Absolute imports successful!")
except ImportError as e:
    print(f"DEBUG: Absolute imports failed: {e}")
    
    # Calculate paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: current_dir: {current_dir}")
    
    # Go up: mcp_server.py -> server -> mcp_postal_geocoder -> src -> project_root
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    print(f"DEBUG: calculated src_dir: {src_dir}")
    print(f"DEBUG: src_dir exists: {os.path.exists(src_dir)}")
    
    # List contents of src_dir
    if os.path.exists(src_dir):
        print(f"DEBUG: Contents of src_dir: {os.listdir(src_dir)}")
    
    # Add src to path
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"DEBUG: Added {src_dir} to sys.path")
    
    print(f"DEBUG: Updated sys.path: {sys.path}")
    
    # Try imports again
    try:
        print("DEBUG: Attempting imports after path modification...")
        from mcp_postal_geocoder.server.database.connection import DatabaseConnection
        from mcp_postal_geocoder.server.database.queries import PostalQueries
        from mcp_postal_geocoder.server.database.models import PostalSearchInput, ReverseGeocodeInput
        print("DEBUG: Imports successful after path modification!")
    except ImportError as e2:
        print(f"DEBUG: Imports still failed: {e2}")
        
        # Last resort: try relative imports
        print("DEBUG: Attempting relative imports...")
        try:
            from .database.connection import DatabaseConnection
            from .database.queries import PostalQueries
            from .database.models import PostalSearchInput, ReverseGeocodeInput
            print("DEBUG: Relative imports successful!")
        except ImportError as e3:
            print(f"DEBUG: Relative imports also failed: {e3}")
            raise e3

# Create MCP server
mcp = FastMCP("postal-geocoder")

# Initialize database components
queries = PostalQueries()

# Database now has correct states, so we can use them directly

@mcp.tool()
def postal_code_search(
    postal_code: str,
    style: str = "MEDIUM"
) -> Dict[str, Any]:
    """Search for a postal code"""
    try:
        params = PostalSearchInput(
            postalcode=postal_code,
            postalcode_startsWith=None,
            country="US",
            maxRows=10,
            style=style
        )
        
        records = queries.search(params)
        
        # Convert to GeoNames-compatible format
        geonames = []
        for record in records:
            item = {
                "postalCode": record.postal_code,
                "lat": record.latitude,
                "lng": record.longitude,
                "countryCode": record.country_code,
                "state": record.state,
                "placeName": record.city or "Unknown"
            }
            
            if style in ["LONG", "FULL"]:
                item.update({
                    "landArea": record.land_area_sqm,
                    "waterArea": record.water_area_sqm
                })
                
            geonames.append(item)
        
        return {
            "totalResultsCount": len(geonames),
            "geonames": geonames
        }
        
    except Exception as e:
        return {"error": str(e), "totalResultsCount": 0, "geonames": []}

@mcp.tool()
def geocode_postal(postalCode: str, style: str = "MEDIUM") -> Dict[str, Any]:
    """Convert postal code to coordinates"""
    try:
        record = queries.find_by_postal_code(postalCode)
        
        if record:
            item = {
                "postalCode": record.postal_code,
                "lat": record.latitude,
                "lng": record.longitude,
                "countryCode": record.country_code,
                "state": record.state,
                "placeName": record.city or "Unknown"
            }
            
            if style in ["LONG", "FULL"]:
                item.update({
                    "landArea": record.land_area_sqm,
                    "waterArea": record.water_area_sqm
                })
            
            return {
                "totalResultsCount": 1,
                "geonames": [item]
            }
        else:
            return {"totalResultsCount": 0, "geonames": []}
            
    except Exception as e:
        return {"error": str(e), "totalResultsCount": 0, "geonames": []}

@mcp.tool()
def reverse_geocode(
    latitude: float,
    longitude: float,
    radius: float = 5.0,
    maxResults: int = 10,
    style: str = "MEDIUM"
) -> Dict[str, Any]:
    """Find postal codes near coordinates"""
    try:
        params = ReverseGeocodeInput(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            maxResults=maxResults
        )
        
        results = queries.find_near_coordinates(params)
        
        geonames = []
        for result in results:
            item = {
                "postalCode": result["zcta_code"],
                "lat": result["latitude"],
                "lng": result["longitude"],
                "countryCode": result["country_code"],
                "state": result["state"],
                "placeName": result.get("city", "Unknown"),
                "distance": result.get("distance", 0)
            }
            
            if style in ["LONG", "FULL"]:
                item.update({
                    "landArea": result.get("land_area_sqm", 0),
                    "waterArea": result.get("water_area_sqm", 0)
                })
                
            geonames.append(item)
        
        return {
            "totalResultsCount": len(geonames),
            "geonames": geonames
        }
        
    except Exception as e:
        return {"error": str(e), "totalResultsCount": 0, "geonames": []}

@mcp.tool()
def validate_postal(postalCode: str) -> Dict[str, Any]:
    """Validate if postal code exists"""
    try:
        is_valid = queries.validate_postal_code(postalCode)
        return {
            "postalCode": postalCode,
            "valid": is_valid
        }
    except Exception as e:
        return {
            "postalCode": postalCode,
            "valid": False,
            "error": str(e)
        }

@mcp.tool()
def postal_stats() -> Dict[str, Any]:
    """Get database statistics and health information"""
    try:
        return queries.get_stats()
    except Exception as e:
        return {"error": str(e), "status": "error"}

def main() -> None:
    """Entry point for the MCP server."""
    # Initialize database connection
    db_conn = DatabaseConnection()
    db_conn.connect()
    
    print("Starting MCP Postal Geocoder Server...")
    mcp.run()

if __name__ == "__main__":
    main()