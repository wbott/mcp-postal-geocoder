"""Response formatting utilities for GeoNames compatibility."""

from typing import List, Dict, Any, Optional
from ..database.models import PostalCodeRecord, GeoNamesResult, GeoNamesResponse, STATE_NAMES


class ResponseFormatter:
    """Format database results into GeoNames-compatible responses."""
    
    @staticmethod
    def format_postal_record(
        record: PostalCodeRecord,
        style: str = "MEDIUM",
        distance: Optional[float] = None
    ) -> GeoNamesResult:
        """Convert PostalCodeRecord to GeoNamesResult format."""
        result = GeoNamesResult(
            postalCode=record.zcta_code,
            countryCode=record.country_code,
            lat=record.latitude,
            lng=record.longitude,
            adminCode1=record.state,
            adminName1=STATE_NAMES.get(record.state, record.state),
        )
        
        if distance is not None:
            result.distance = distance
        
        if style in ["MEDIUM", "LONG", "FULL"]:
            result.landArea = record.land_area_sqm
            result.waterArea = record.water_area_sqm
        
        return result
    
    @staticmethod
    def format_response(
        records: List[PostalCodeRecord],
        style: str = "MEDIUM",
        distances: Optional[List[float]] = None
    ) -> GeoNamesResponse:
        """Format multiple records into GeoNames response."""
        geonames = []
        
        for i, record in enumerate(records):
            distance = distances[i] if distances and i < len(distances) else None
            formatted = ResponseFormatter.format_postal_record(record, style, distance)
            geonames.append(formatted)
        
        return GeoNamesResponse(
            totalResultsCount=len(geonames),
            geonames=geonames
        )
    
    @staticmethod
    def format_reverse_geocode_response(
        results: List[Dict[str, Any]],
        style: str = "MEDIUM"
    ) -> GeoNamesResponse:
        """Format reverse geocode results with distances."""
        geonames = []
        
        for result in results:
            # Convert dict result to PostalCodeRecord
            record = PostalCodeRecord(
                zcta_code=result['zcta_code'],
                latitude=result['latitude'],
                longitude=result['longitude'],
                state=result['state'],
                land_area_sqm=result['land_area_sqm'],
                water_area_sqm=result['water_area_sqm'],
                country_code=result.get('country_code', 'US')
            )
            
            formatted = ResponseFormatter.format_postal_record(
                record, 
                style, 
                result.get('distance')
            )
            geonames.append(formatted)
        
        return GeoNamesResponse(
            totalResultsCount=len(geonames),
            geonames=geonames
        )