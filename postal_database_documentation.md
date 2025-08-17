# Postal Code SQLite Database Documentation

## Overview
This SQLite database contains comprehensive US postal code data derived from the US Census Bureau's 2020 ZIP Code Tabulation Areas (ZCTAs). The database is optimized for MCP (Model Context Protocol) server geocoding operations.

## Database File Details
- **File Size**: ~3.3 MB
- **Format**: SQLite 3.x
- **Records**: 33,791 ZIP Code Tabulation Areas
- **Coverage**: Complete populated areas across all 50 US states + territories
- **Data Source**: US Census Bureau TIGER/Line Shapefiles (2020 Census)
- **Legal Status**: Public domain (no attribution required)

## Schema Structure

### Main Table: `postal_codes`

| Column | Type | Nullable | Description | Example |
|--------|------|----------|-------------|---------|
| `id` | INTEGER | No | Primary key (auto-increment) | 1, 2, 3... |
| `zcta_code` | TEXT | No | 5-digit ZIP Code Tabulation Area code | "90210", "10001" |
| `zip` | TEXT | Yes | Alias for zcta_code (for compatibility) | "90210", "10001" |
| `postal_code` | TEXT | Yes | Another alias for zcta_code | "90210", "10001" |
| `latitude` | REAL | Yes | Centroid latitude (WGS84) | 34.0901, 40.7505 |
| `longitude` | REAL | Yes | Centroid longitude (WGS84) | -118.4065, -73.9934 |
| `country_code` | TEXT | Yes | ISO country code (always "US") | "US" |
| `state` | TEXT | Yes | Regional grouping based on ZIP range | "AK/CA/HI/OR/WA" |
| `land_area_sqm` | REAL | Yes | Land area in square meters | 1029067.0 |
| `water_area_sqm` | REAL | Yes | Water area in square meters | 0.0 |

### Indexes (Performance Optimized)
```sql
-- Primary lookups
CREATE INDEX idx_zcta_lookup ON postal_codes(zcta_code);
CREATE INDEX idx_zip ON postal_codes(zip);
CREATE INDEX idx_postal_code ON postal_codes(postal_code);

-- Geographic operations
CREATE INDEX idx_coordinates ON postal_codes(latitude, longitude);
CREATE INDEX idx_country_zcta ON postal_codes(country_code, zcta_code);

-- Administrative filtering
CREATE INDEX idx_state ON postal_codes(state);
```

### Views Available

#### `active_postal_codes`
Provides standardized column names for compatibility:
```sql
SELECT 
    zcta_code as zip,
    zcta_code as postal_code,
    country_code,
    state,
    latitude,
    longitude,
    land_area_sqm,
    water_area_sqm
FROM postal_codes;
```

#### `postal_by_state`
State-level statistics:
```sql
SELECT 
    state,
    COUNT(*) as zip_count
FROM postal_codes 
GROUP BY state
ORDER BY zip_count DESC;
```

## Geographic Coverage

### ZIP Code Ranges
The database covers all 10 US ZIP code ranges:

| Range | Region | Example States | Count |
|-------|--------|----------------|-------|
| 0xxxx | Northeast | CT, MA, ME, NH, NJ, RI, VT | ~3,400 |
| 1xxxx | Northeast | DE, NY, PA | ~4,600 |
| 2xxxx | South | DC, MD, NC, SC, VA, WV | ~3,200 |
| 3xxxx | South | AL, FL, GA, MS, TN | ~3,800 |
| 4xxxx | Midwest | IN, KY, MI, OH | ~3,600 |
| 5xxxx | Midwest | IA, MN, MT, ND, SD, WI | ~2,800 |
| 6xxxx | South | IL, KS, MO, NE | ~2,900 |
| 7xxxx | South | AR, LA, OK, TX | ~4,100 |
| 8xxxx | West | AZ, CO, ID, NM, NV, UT, WY | ~2,700 |
| 9xxxx | West | AK, CA, HI, OR, WA | ~2,800 |

### Coordinate Bounds
- **Latitude**: 18.9° to 71.4° (US Virgin Islands to Northern Alaska)
- **Longitude**: -179.1° to -65.2° (Aleutian Islands to US Virgin Islands)
- **Coordinate System**: WGS84 (EPSG:4326)

## Performance Characteristics

### Query Performance
- **ZIP code lookup**: <1ms average
- **Proximity search**: 10-50ms (depending on radius)
- **Bulk operations**: Highly optimized with proper indexing
- **Memory usage**: ~64MB cache configured by default

### Optimal Query Patterns
```sql
-- Fast ZIP code lookup (uses index)
SELECT * FROM postal_codes WHERE zcta_code = '90210';

-- Geographic search (bounding box recommended)
SELECT * FROM postal_codes 
WHERE latitude BETWEEN 34.0 AND 35.0 
  AND longitude BETWEEN -119.0 AND -118.0;

-- Proximity search (simplified)
SELECT *, 
       ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) as distance_sq
FROM postal_codes 
WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
ORDER BY distance_sq LIMIT 10;
```

## MCP Server Integration Guidelines

### Recommended MCP Tools

1. **geocode_postal**
   - Input: ZIP code string
   - Output: Coordinates, state, metadata
   - Use case: Address geocoding

2. **reverse_geocode**
   - Input: Latitude, longitude, radius
   - Output: Nearby ZIP codes with distances
   - Use case: Location-based services

3. **validate_postal**
   - Input: ZIP code string
   - Output: Boolean validation result
   - Use case: Form validation

4. **postal_stats**
   - Input: None
   - Output: Database statistics
   - Use case: System health checks

### Connection Setup
```python
import sqlite3

# Recommended connection setup
conn = sqlite3.connect('postal_census_complete.db')
conn.row_factory = sqlite3.Row  # Enable column access by name

# Performance optimizations
conn.execute('PRAGMA optimize')
conn.execute('PRAGMA cache_size = -64000')  # 64MB cache
conn.execute('PRAGMA journal_mode = WAL')
```

### Error Handling Considerations
- **Missing ZIP codes**: Not all USPS ZIP codes have ZCTAs (PO Box only, military)
- **Coordinate precision**: Centroids are approximate (good for city-level accuracy)
- **Temporal accuracy**: Data reflects January 1, 2020 boundaries
- **State field**: Regional groupings, not exact state assignments

## Data Quality Notes

### Strengths
✅ **Complete coverage** of populated areas  
✅ **Official source** (US Census Bureau)  
✅ **High coordinate accuracy** (calculated centroids)  
✅ **Consistent format** across all records  
✅ **No missing coordinates** in any record  

### Limitations
⚠️ **ZCTA vs ZIP**: ZCTAs approximate ZIP codes but aren't identical  
⚠️ **No city names**: ZCTA data doesn't include city/place names  
⚠️ **No street addresses**: Only area-level data  
⚠️ **2020 snapshot**: Boundaries may have changed since then  
⚠️ **US only**: No international postal codes  

## Sample Queries for MCP Operations

### Basic Geocoding
```sql
-- Geocode a ZIP code
SELECT zcta_code, latitude, longitude, state 
FROM postal_codes 
WHERE zcta_code = '90210';
```

### Reverse Geocoding
```sql
-- Find nearest ZIP codes to coordinates
SELECT zcta_code, latitude, longitude,
       ((latitude - 34.0522) * (latitude - 34.0522) + 
        (longitude - (-118.2437)) * (longitude - (-118.2437))) as distance_sq
FROM postal_codes 
WHERE latitude BETWEEN 33.5522 AND 34.5522
  AND longitude BETWEEN -118.7437 AND -117.7437
ORDER BY distance_sq 
LIMIT 5;
```

### Validation
```sql
-- Check if ZIP code exists
SELECT EXISTS(
    SELECT 1 FROM postal_codes WHERE zcta_code = '12345'
) as is_valid;
```

### Regional Queries
```sql
-- Get all ZIP codes in West region
SELECT zcta_code, latitude, longitude 
FROM postal_codes 
WHERE zcta_code LIKE '9%' 
ORDER BY zcta_code;
```

## Best Practices for MCP Implementation

### Performance Tips
1. **Use prepared statements** for repeated queries
2. **Implement connection pooling** for concurrent requests
3. **Cache frequent lookups** in memory
4. **Use bounding box searches** before distance calculations
5. **Limit result sets** with appropriate LIMIT clauses

### Accuracy Considerations
1. **ZCTA centroids** represent geographic centers, not delivery points
2. **Coordinate precision** is suitable for city/neighborhood level accuracy
3. **Distance calculations** should account for Earth's curvature for precision
4. **Validation responses** should note ZCTA vs ZIP code differences

### Error Handling
1. **Invalid ZIP codes** should return empty results, not errors
2. **Out-of-bounds coordinates** should be handled gracefully
3. **Database connection failures** need proper retry logic
4. **Empty result sets** should return structured responses

## Integration Examples

### Python MCP Server Skeleton
```python
class PostalCodeMCP:
    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
    
    def geocode(self, zip_code):
        cursor = self.db.execute(
            "SELECT zcta_code, latitude, longitude, state FROM postal_codes WHERE zcta_code = ?",
            (zip_code,)
        )
        return cursor.fetchone()
    
    def reverse_geocode(self, lat, lon, radius_km=5):
        # Implementation with bounding box + distance calculation
        pass
```

### TypeScript/JavaScript Example
```javascript
import Database from 'better-sqlite3';

class PostalCodeMCP {
    constructor(dbPath) {
        this.db = new Database(dbPath);
        this.db.pragma('optimize');
    }
    
    geocode(zipCode) {
        const stmt = this.db.prepare(
            'SELECT zcta_code, latitude, longitude, state FROM postal_codes WHERE zcta_code = ?'
        );
        return stmt.get(zipCode);
    }
}
```

## Maintenance and Updates

### Database Freshness
- **Current data**: Based on 2020 Census (most recent available)
- **Update frequency**: Census updates ZCTAs every 10 years
- **Next update**: Expected around 2030 Census

### File Management
- **Backup recommendations**: SQLite file is self-contained
- **Version control**: Consider tracking schema migrations
- **Size monitoring**: Database should remain under 5MB

---

**Data Attribution**: US Census Bureau ZIP Code Tabulation Areas (2020 Census)  
**License**: Public domain (US Government work)  
**Last Updated**: [Current Date]