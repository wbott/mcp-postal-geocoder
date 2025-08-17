---
title: MCP Postal Geocoder
emoji: 📍
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: "1.28.0"
app_file: streamlit_app.py
pinned: false
---

# MCP Postal Geocoder

**Model Context Protocol (MCP) Server for US Postal Code Geocoding**

A drop-in replacement for GeoNames postal code API using US Census Bureau ZIP Code Tabulation Areas (ZCTAs). 
Fast, accurate, and comprehensive with 33,791 US postal codes.

## 🌟 Features

- **5 MCP Tools**: Search, geocode, reverse geocode, validate, and statistics
- **Census Accuracy**: Official US Census Bureau ZCTA data
- **High Performance**: <1ms exact lookups, <50ms reverse geocoding
- **Complete Coverage**: All 33,791 US postal codes with cities and states
- **FastMCP Framework**: Modern, efficient MCP server implementation

## 🚀 Demo

Try the live demo: [**MCP Postal Geocoder on HuggingFace Spaces**](https://huggingface.co/spaces/bott-wa/mcp-postal-geocoder)

### Features in Demo:
- **📊 Database Statistics** - Real-time stats on 33,791 postal codes
- **🔍 Search Tools** - Exact match and prefix search with maps
- **🌍 Geocoding** - Convert postal codes to coordinates
- **📍 Reverse Geocoding** - Find postal codes near any location
- **✅ Validation** - Quick postal code validation

## 🛠️ Available Tools

1. **postal_code_search** - Search postal codes (exact match or prefix)
2. **geocode_postal** - Convert postal code to coordinates
3. **reverse_geocode** - Find postal codes near coordinates
4. **validate_postal** - Check if postal code exists
5. **postal_stats** - Database statistics and health

## 📦 Installation

```bash
pip install -e .
```

## 🎯 Usage

### MCP Server
```bash
# Start MCP server
mcp-postal-server

# Or with Python
python -m mcp_postal_geocoder.server.mcp_server
```

### CLI Client
```bash
# Test all tools
postal-cli test

# Individual commands
postal-cli geocode 90210
postal-cli reverse 47.606 -122.332
postal-cli stats
```

### Streamlit Demo
```bash
streamlit run streamlit_app.py
```

## 🗂️ Database Schema

- **zcta_code** (TEXT) - 5-digit ZIP code (primary key)
- **latitude**, **longitude** (REAL) - WGS84 coordinates  
- **state** (TEXT) - State abbreviation
- **city** (TEXT) - City name
- **land_area_sqm**, **water_area_sqm** (REAL) - Area measurements
- **country_code** (TEXT) - Always "US"

## 🔧 Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Lint and format  
ruff check src/
black src/
mypy src/
```

## 📊 Performance

- **Exact postal code lookup**: <1ms
- **Prefix searches**: <10ms
- **Reverse geocoding**: <50ms
- **Concurrent connections**: 100+
- **Database size**: 6.9MB SQLite

## 🏗️ Architecture

```
src/mcp_postal_geocoder/
├── server/
│   ├── mcp_server.py          # Main MCP server (FastMCP)
│   ├── database/
│   │   ├── connection.py      # SQLite connection management
│   │   ├── models.py          # Pydantic data models
│   │   └── queries.py         # Optimized SQL queries
│   └── utils/
│       └── formatters.py      # Response formatting
├── client/
│   └── cli_tool.py           # CLI client for testing
└── data/
    └── postal_census_complete.db  # SQLite database (33,791 records)
```

## 🌐 API Compatibility

Designed as a drop-in replacement for GeoNames postal API:

```json
{
  "totalResultsCount": 1,
  "geonames": [
    {
      "postalCode": "90210",
      "lat": 34.102512,
      "lng": -118.415075,
      "countryCode": "US", 
      "state": "CA",
      "placeName": "Santa Monica"
    }
  ]
}
```

## 📄 License

MIT License - see LICENSE file for details.

## 🚀 Deployment

### HuggingFace Spaces
1. Create a new Space on HuggingFace with Streamlit SDK
2. Copy files: `streamlit_app.py`, `requirements.txt`, `src/`, `data/`
3. Use `space_config.yml` for Space configuration
4. Or use the GitHub Action for automatic sync

### GitHub Action Setup
1. Add `HF_TOKEN` to GitHub repository secrets
2. Update USERNAME/SPACENAME in `.github/workflows/sync-to-hf.yml`
3. Push to main branch triggers automatic deployment

### Local Development
```bash
streamlit run streamlit_app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📈 Status

- ✅ **Phase 1**: Core MCP server implementation
- ✅ **Phase 2**: Advanced search and city assignments  
- ✅ **Phase 3**: CLI client and testing tools
- ✅ **Phase 4**: Streamlit demo and deployment
- 🔄 **Phase 5**: Documentation and optimization

## 🙏 Acknowledgments

- US Census Bureau for ZCTA data
- Anthropic for MCP framework
- FastMCP for modern server implementation