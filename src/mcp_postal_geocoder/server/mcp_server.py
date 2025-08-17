"""MCP server implementation for postal code geocoding using FastMCP."""

from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from mcp_postal_geocoder.server.database.connection import DatabaseConnection
from mcp_postal_geocoder.server.database.queries import PostalQueries
from mcp_postal_geocoder.server.database.models import PostalSearchInput, ReverseGeocodeInput

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