"""Data models and validation schemas for postal code operations."""

from typing import Optional, Literal, List
from pydantic import BaseModel, Field, validator
import sqlite3


class PostalCodeRecord(BaseModel):
    """Database record for a postal code."""
    zcta_code: str
    latitude: float
    longitude: float
    state: str
    land_area_sqm: float
    water_area_sqm: float
    country_code: str = "US"
    city: Optional[str] = None
    
    @property
    def postal_code(self) -> str:
        """Get postal code (alias for zcta_code)."""
        return self.zcta_code


class GeoNamesResult(BaseModel):
    """GeoNames-compatible result format."""
    postalCode: str
    placeName: Optional[str] = None
    countryCode: str
    lat: float
    lng: float
    adminCode1: str
    adminName1: str
    distance: Optional[float] = None
    landArea: Optional[float] = None
    waterArea: Optional[float] = None


class GeoNamesResponse(BaseModel):
    """GeoNames-compatible response format."""
    totalResultsCount: int
    geonames: List[GeoNamesResult]


class PostalSearchInput(BaseModel):
    """Input parameters for postal code search."""
    postalcode: Optional[str] = None
    postalcode_startsWith: Optional[str] = None
    placename: Optional[str] = None
    placename_startsWith: Optional[str] = None
    country: Optional[Literal["US"]] = None
    countryBias: Optional[str] = None
    maxRows: int = Field(default=10, ge=1, le=100)
    style: Literal["SHORT", "MEDIUM", "LONG", "FULL"] = "MEDIUM"
    operator: Literal["AND", "OR"] = "AND"


class ReverseGeocodeInput(BaseModel):
    """Input parameters for reverse geocoding."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius: float = Field(default=5.0, ge=0.1, le=100)
    maxResults: int = Field(default=10, ge=1, le=100)


# State code mapping for adminName1 field
STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
    'PR': 'Puerto Rico', 'VI': 'U.S. Virgin Islands', 'AS': 'American Samoa',
    'GU': 'Guam', 'MP': 'Northern Mariana Islands'
}


def row_to_postal_record(row: sqlite3.Row) -> PostalCodeRecord:
    """Convert SQLite row to PostalCodeRecord."""
    return PostalCodeRecord(
        zcta_code=row['zcta_code'],
        latitude=row['latitude'],
        longitude=row['longitude'],
        state=row['state'],
        land_area_sqm=row['land_area_sqm'],
        water_area_sqm=row['water_area_sqm'],
        country_code=row['country_code'] if 'country_code' in row.keys() else 'US',
        city=row['city'] if 'city' in row.keys() else None
    )