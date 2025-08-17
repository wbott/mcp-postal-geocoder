# MCP Postal Geocoder Project

This is an MCP (Model Context Protocol) server for US postal code geocoding using Census ZCTA data.

## Project Overview

**Purpose**: Drop-in replacement for GeoNames postal code API using US Census Bureau ZIP Code Tabulation Areas (ZCTAs).

**Technology Stack**: Python 3.9+, SQLite, MCP SDK, Pydantic

**Database**: 33,791 US postal code records in `data/postal_census_complete.db`

## Project Structure

- `src/mcp_postal_geocoder/` - Main Python package
  - `server/` - MCP server implementation
    - `database/` - Database connection, models, queries
    - `mcp_server.py` - Main MCP server with 5 tools
    - `utils/` - Response formatting utilities
  - `client/` - CLI tool for testing
- `data/` - SQLite database file
- `tests/` - Unit, integration, and performance tests

## MCP Tools Available

1. **postalCodeSearch** - Search postal codes (exact match or prefix)
2. **geocodePostal** - Convert postal code to coordinates  
3. **reverseGeocode** - Find postal codes near coordinates
4. **validatePostal** - Check if postal code exists
5. **postalStats** - Database statistics and health

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run MCP server
python -m mcp_postal_geocoder.server.mcp_server

# OR use entry point
mcp-postal-server

# Run CLI tool
postal-cli stats

# Run tests (when implemented)
pytest

# Lint and format
ruff check src/
black src/
mypy src/
```

## Database Schema

Table: `postal_codes`
- `zcta_code` (TEXT) - 5-digit ZIP code (primary key)
- `latitude`, `longitude` (REAL) - WGS84 coordinates
- `state` (TEXT) - State abbreviation
- `land_area_sqm`, `water_area_sqm` (REAL) - Area measurements
- `country_code` (TEXT) - Always "US"

## Implementation Status

✅ **Phase 1 Complete**: Basic project structure, database layer, MCP server framework
⏳ **Phase 2 Pending**: Advanced search features, testing, optimization
⏳ **Phase 3 Pending**: Full GeoNames API compatibility
⏳ **Phase 4 Pending**: Client tools, documentation, deployment

## Performance Targets

- Exact postal code lookup: <1ms
- Prefix searches: <10ms  
- Reverse geocoding: <50ms
- Concurrent connections: 100+

## Key Files

- `pyproject.toml` - Python package configuration
- `mcp_postal_code_plan.md` - Detailed implementation plan
- `postal_database_documentation.md` - Database schema details
- `src/mcp_postal_geocoder/server/mcp_server.py` - Main server implementation