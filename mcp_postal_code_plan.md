# MCP Postal Code Server - Implementation Plan

## Project Overview

**Objective**: Build an MCP (Model Context Protocol) server and client that mirrors the GeoNames postal code search API functionality for US postal codes.

**Data Source**: SQLite database with US Census Bureau ZIP Code Tabulation Areas (ZCTAs) - 33,791 records covering all populated US areas.

**Target Compatibility**: Drop-in replacement for GeoNames postal code API calls within the US.

## Repository Structure

```
mcp-postal-server/
├── README.md
├── package.json / pyproject.toml
├── src/
│   ├── server/
│   │   ├── mcp_server.py/ts          # Main MCP server implementation
│   │   ├── database/
│   │   │   ├── connection.py/ts      # Database connection management
│   │   │   ├── queries.py/ts         # Optimized SQL queries
│   │   │   └── models.py/ts          # Data models and schemas
│   │   ├── tools/
│   │   │   ├── postal_search.py/ts   # postalCodeSearch tool
│   │   │   ├── geocode.py/ts         # geocodePostal tool
│   │   │   ├── reverse_geocode.py/ts # reverseGeocode tool
│   │   │   ├── validate.py/ts        # validatePostal tool
│   │   │   └── stats.py/ts           # postalStats tool
│   │   └── utils/
│   │       ├── response_formatter.py/ts # GeoNames format compatibility
│   │       ├── validators.py/ts      # Input validation
│   │       └── distance.py/ts        # Geographic distance calculations
├── client/
│   ├── example_client.py/ts          # Example MCP client usage
│   └── cli_tool.py/ts                # Command-line interface
├── data/
│   └── postal_census_complete.db     # SQLite database file
├── tests/
│   ├── unit/                         # Unit tests for each component
│   ├── integration/                  # End-to-end MCP tests
│   └── performance/                  # Load and performance tests
├── docs/
│   ├── api_reference.md              # Complete API documentation
│   ├── database_schema.md            # Database structure details
│   └── deployment_guide.md           # Production deployment guide
└── scripts/
    ├── setup_database.py/ts          # Database initialization
    └── benchmark.py/ts               # Performance testing
```

## Technical Specifications

### Core Technologies

**Language Options**: Python 3.9+ or TypeScript/Node.js 18+
**Database**: SQLite 3.x with WAL mode for concurrent access
**MCP Framework**: Official Anthropic MCP SDK
**Performance**: Target <1ms postal code lookups, <100ms geographic searches

### Database Schema Integration

The existing SQLite database (`postal_census_complete.db`) contains:

**Main Table**: `postal_codes`
- `zcta_code` (TEXT): 5-digit ZIP code (primary lookup field)
- `latitude`, `longitude` (REAL): WGS84 coordinates  
- `state` (TEXT): Regional grouping
- `land_area_sqm`, `water_area_sqm` (REAL): Area measurements
- `country_code` (TEXT): Always "US"

**Key Indexes** (already optimized):
- `idx_zcta_lookup`: Fast postal code searches
- `idx_coordinates`: Geographic range queries
- `idx_country_zcta`: Country-filtered searches

## MCP Tools Implementation

### 1. postalCodeSearch Tool

**Primary Function**: Main search functionality matching GeoNames API

```typescript
interface PostalSearchInput {
  postalcode?: string;              // Exact postal code
  postalcode_startsWith?: string;   // Prefix search
  placename?: string;               // Place name (limited support)
  placename_startsWith?: string;    // Place name prefix
  country?: "US";                   // Country filter (US only initially)
  countryBias?: string;             // Priority country
  maxRows?: number;                 // Result limit (1-100, default 10)
  style?: "SHORT" | "MEDIUM" | "LONG" | "FULL"; // Response verbosity
  operator?: "AND" | "OR";          // Multi-term search logic
}
```

**SQL Implementation Strategy**:
```sql
-- Exact match (fastest path)
SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm
FROM postal_codes 
WHERE zcta_code = ?

-- Prefix search with limit
SELECT zcta_code, latitude, longitude, state, land_area_sqm, water_area_sqm
FROM postal_codes 
WHERE zcta_code LIKE ? || '%'
ORDER BY zcta_code
LIMIT ?
```

### 2. geocodePostal Tool

**Purpose**: Convert postal code to coordinates
**Input**: Single postal code string
**Output**: Coordinates with administrative data

```typescript
interface GeocodeResult {
  postalCode: string;
  latitude: number;
  longitude: number;
  countryCode: "US";
  adminCode1: string;    // State abbreviation
  adminName1: string;    // Full state name
  landArea?: number;
  waterArea?: number;
}
```

### 3. reverseGeocode Tool

**Purpose**: Find postal codes near coordinates
**Algorithm**: Bounding box + distance calculation for performance

```typescript
interface ReverseGeocodeInput {
  latitude: number;
  longitude: number;
  radius?: number;       // Radius in kilometers (default 5)
  maxResults?: number;   // Limit results (default 10)
}
```

**Implementation Pattern**:
```sql
-- Optimized reverse geocoding with bounding box pre-filter
SELECT zcta_code, latitude, longitude, state,
       SQRT((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) * 111.32 as distance_km
FROM postal_codes 
WHERE latitude BETWEEN ? AND ? 
  AND longitude BETWEEN ? AND ?
  AND SQRT((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) * 111.32 <= ?
ORDER BY distance_km 
LIMIT ?
```

### 4. validatePostal Tool

**Purpose**: Fast postal code validation
**Implementation**: Simple existence check with boolean response

### 5. postalStats Tool

**Purpose**: Database health and statistics
**Output**: Record counts, database size, index status

## Response Format Specifications

### GeoNames Compatibility

**JSON Response Structure**:
```json
{
  "totalResultsCount": 1,
  "geonames": [
    {
      "postalCode": "90210",
      "placeName": "Beverly Hills",  // Limited availability in ZCTA data
      "countryCode": "US",
      "lat": 34.0901,
      "lng": -118.4065,
      "adminCode1": "CA",
      "adminName1": "California",
      "distance": 0.0,              // For reverse geocoding only
      "landArea": 1029067.0,
      "waterArea": 0.0
    }
  ]
}
```

**Style Variations**:
- **SHORT**: `postalCode`, `lat`, `lng` only
- **MEDIUM**: Add administrative codes and areas
- **LONG**: Include all metadata and statistics  
- **FULL**: Add database-specific fields and query performance data

**XML Support**: Optional XML output for full GeoNames compatibility

## Performance Requirements

### Target Metrics

- **Exact postal code lookup**: <1ms average response time
- **Prefix searches**: <10ms for reasonable result sets
- **Reverse geocoding**: <50ms within 10km radius
- **Concurrent connections**: Support 100+ simultaneous requests
- **Memory usage**: <128MB baseline, <512MB under load

### Optimization Strategies

1. **Connection Pooling**: Reuse SQLite connections with WAL mode
2. **Query Optimization**: Use prepared statements and proper indexes
3. **Result Caching**: Cache frequent lookups in memory (LRU)
4. **Batch Processing**: Support bulk geocoding requests
5. **Geographic Indexing**: Implement spatial partitioning for large radius searches

## Implementation Phases

### Phase 1: Core MCP Server (Week 1-2)
- [ ] Set up MCP server framework
- [ ] Implement database connection with pooling
- [ ] Create basic `postalCodeSearch` tool (exact match only)
- [ ] Add `geocodePostal` functionality
- [ ] Implement JSON response formatting
- [ ] Basic error handling and validation

**Deliverable**: Working MCP server with exact postal code lookups

### Phase 2: Advanced Search Features (Week 3-4)
- [ ] Add "starts with" pattern searches
- [ ] Implement `reverseGeocode` tool with distance calculations
- [ ] Add `validatePostal` and `postalStats` tools
- [ ] Optimize query performance and add caching
- [ ] Comprehensive input validation and error handling
- [ ] Unit test coverage for all tools

**Deliverable**: Feature-complete MCP server with all search patterns

### Phase 3: GeoNames API Compatibility (Week 5-6)
- [ ] Match exact GeoNames response format
- [ ] Implement all style variations (SHORT, MEDIUM, LONG, FULL)
- [ ] Add XML output option
- [ ] Place name search (limited by ZCTA data constraints)
- [ ] Performance benchmarking and optimization
- [ ] Integration testing with existing GeoNames clients

**Deliverable**: Drop-in replacement for GeoNames postal code API

### Phase 4: Client Tools and Documentation (Week 7-8)
- [ ] Create example MCP client implementations
- [ ] Build command-line interface tool
- [ ] Comprehensive API documentation
- [ ] Deployment guide and Docker containers
- [ ] Performance testing and load testing
- [ ] Production readiness checklist

**Deliverable**: Production-ready package with client tools and docs

## Data Limitations and Mitigation

### Known Limitations

1. **No city/place names**: ZCTA data lacks municipal names
2. **ZCTA vs ZIP discrepancy**: Some USPS ZIP codes don't have ZCTAs
3. **2020 data snapshot**: Boundaries may have changed since census
4. **US only**: No international postal codes initially

### Mitigation Strategies

1. **City Name Mapping**: Create supplementary city-to-ZIP lookup table
2. **USPS Integration**: Option to supplement with official USPS data
3. **Fuzzy Matching**: Implement approximate string matching for place names
4. **Data Freshness**: Document data vintage and update procedures
5. **Clear Limitations**: Document exact capabilities vs GeoNames API

## Error Handling Strategy

### Error Categories and Responses

```typescript
interface ErrorResponse {
  status: "error";
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable description
    details?: object;       // Additional context
  };
}
```

**Error Codes**:
- `INVALID_POSTAL_CODE`: Malformed postal code format
- `NO_RESULTS_FOUND`: Valid input but no matching records
- `INVALID_COORDINATES`: Out-of-range latitude/longitude
- `DATABASE_ERROR`: Connection or query failures
- `RATE_LIMIT_EXCEEDED`: Too many requests from client
- `INVALID_PARAMETERS`: Missing required parameters or invalid values

## Testing Strategy

### Unit Tests
- Individual tool functionality with mock database
- SQL query correctness and performance
- Response format validation against schemas
- Error handling for all failure scenarios

### Integration Tests  
- End-to-end MCP protocol communication
- Database connection reliability under load
- Cross-platform compatibility (Windows, macOS, Linux)
- Memory leak detection during extended runs

### Performance Tests
- Load testing with concurrent connections
- Query performance benchmarking
- Memory usage profiling
- Response time percentile analysis

### Compatibility Tests
- GeoNames API response format matching
- Client library compatibility testing
- Backward compatibility with API changes

## Security and Production Considerations

### Security Measures
- **Input Sanitization**: Validate and sanitize all user inputs
- **SQL Injection Prevention**: Use parameterized queries exclusively
- **Rate Limiting**: Implement request throttling to prevent abuse
- **Resource Limits**: Set maximum result set sizes and query timeouts

### Production Deployment
- **Container Support**: Docker images for easy deployment
- **Health Checks**: Endpoints for monitoring database and server health
- **Logging**: Structured logging for debugging and monitoring
- **Configuration**: Environment-based configuration management
- **Monitoring**: Metrics collection for performance tracking

## Extension Points for Future Development

### International Expansion
- **Schema Extension**: Add support for international postal codes
- **Data Integration**: Connect to international postal databases
- **Localization**: Support multiple languages and regional formats

### Enhanced Features
- **Timezone Data**: Add timezone information to postal code responses
- **Demographic Data**: Include population and economic indicators
- **Boundary Data**: Add polygon boundaries for ZIP code areas
- **Real-time Updates**: Support dynamic data updates and notifications

### Performance Enhancements
- **Spatial Indexing**: Implement R-tree or similar spatial indexes
- **Distributed Caching**: Redis or similar for multi-instance deployments
- **Database Sharding**: Partition data for extreme scale requirements
- **CDN Integration**: Cache responses at edge locations

## Success Criteria

### Functional Requirements
- [ ] 100% compatibility with GeoNames postal code search API parameters
- [ ] Response format matches GeoNames structure exactly
- [ ] All 33,791 US postal codes searchable with sub-second response times
- [ ] Reverse geocoding accuracy within 1km for most locations

### Performance Requirements
- [ ] <1ms average response time for exact postal code lookups
- [ ] <100ms average response time for geographic searches
- [ ] Support 100+ concurrent connections without degradation
- [ ] <512MB memory usage under maximum load

### Quality Requirements
- [ ] >95% unit test coverage for all core functionality
- [ ] Zero critical security vulnerabilities in dependency scan
- [ ] Complete API documentation with examples
- [ ] Production deployment guide with monitoring setup

---

**Next Steps**: 
1. Set up development environment and repository structure
2. Initialize MCP server framework with basic tool registration
3. Implement database connection layer with the existing SQLite file
4. Begin Phase 1 implementation with exact postal code search functionality

This implementation plan provides a clear roadmap for building a production-ready MCP postal code server that serves as a drop-in replacement for GeoNames API calls within the United States.