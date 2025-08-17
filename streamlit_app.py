"""Streamlit demo app for MCP Postal Geocoder."""

import streamlit as st
import asyncio
import json
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from typing import Dict, Any, List
import platform

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Page configuration
st.set_page_config(
    page_title="MCP Postal Geocoder Demo",
    page_icon="📮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📮 MCP Postal Geocoder Demo")
st.markdown("""
**Model Context Protocol (MCP) Server for US Postal Code Geocoding**

This demo showcases a drop-in replacement for GeoNames postal code API using US Census Bureau ZIP Code Tabulation Areas (ZCTAs).
All data is sourced from official US Census Bureau records with 33,791 postal codes.
""")

@st.cache_data
def get_python_command() -> str:
    """Get the appropriate Python command for the current platform."""
    return "python" if platform.system() == "Windows" else "python3"

@st.cache_data
def get_server_command() -> tuple:
    """Get the appropriate MCP server command for the current environment.
    
    This function automatically detects the deployment environment and chooses
    the best way to run the MCP server:
    1. Bootstrap script (for containerized environments like Hugging Face Spaces)
    2. Installed package module (for local development)
    3. Direct file execution (fallback)
    """
    import os
    
    # Strategy 1: Try bootstrap script (best for containerized environments)
    bootstrap_script = os.path.join(os.path.dirname(__file__), "run_mcp_server.py")
    if os.path.exists(bootstrap_script):
        return (get_python_command(), [bootstrap_script])
    
    # Strategy 2: Try installed package (local development)
    try:
        import mcp_postal_geocoder
        return (get_python_command(), ["-m", "mcp_postal_geocoder.server.mcp_server"])
    except ImportError:
        # Strategy 3: Direct file execution (fallback)
        server_file = os.path.join("src", "mcp_postal_geocoder", "server", "mcp_server.py")
        return (get_python_command(), [server_file])

async def call_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool and return the result."""
    command, args = get_server_command()
    server_params = StdioServerParameters(
        command=command,
        args=args
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, tool_args)
                
                if result.content:
                    return json.loads(result.content[0].text)
                else:
                    return {"error": "No response received"}
    except Exception as e:
        return {"error": str(e)}

def run_async(coro):
    """Run async function in Streamlit."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Handle if we're already in an async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

# Sidebar navigation
st.sidebar.title("🛠️ Tools")
selected_tool = st.sidebar.selectbox(
    "Choose a tool to demonstrate:",
    [
        "📊 Database Statistics",
        "🔍 Postal Code Search", 
        "🌍 Geocode Postal Code",
        "📍 Reverse Geocoding",
        "✅ Validate Postal Code"
    ]
)

# Database Statistics
if selected_tool == "📊 Database Statistics":
    st.header("📊 Database Statistics")
    st.markdown("Get comprehensive statistics about the postal code database.")
    
    if st.button("Get Database Stats", type="primary"):
        with st.spinner("Fetching database statistics..."):
            result = run_async(call_mcp_tool("postal_stats", {}))
        
        if "error" not in result:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", f"{result['totalRecords']:,}")
            with col2:
                st.metric("Unique States", result['uniqueStates'])
            with col3:
                st.metric("Database Size", f"{result['databaseSize']:,} bytes")
            with col4:
                st.metric("Status", result['status'].title())
                
            st.success("Database is healthy and operational!")
        else:
            st.error(f"Error: {result['error']}")

# Postal Code Search
elif selected_tool == "🔍 Postal Code Search":
    st.header("🔍 Postal Code Search")
    st.markdown("Search for postal codes by exact match or prefix.")
    
    search_type = st.radio(
        "Search Type:",
        ["Exact Match", "Prefix Search"]
    )
    
    if search_type == "Exact Match":
        postal_code = st.text_input("Enter a 5-digit postal code:", placeholder="e.g., 73717")
        if st.button("Search Postal Code", type="primary") and postal_code:
            with st.spinner("Searching..."):
                result = run_async(call_mcp_tool("postal_code_search", {"postal_code": postal_code}))
                st.session_state.search_result = result
                st.session_state.search_postal_code = postal_code
        
        # Display results from session state
        if hasattr(st.session_state, 'search_result'):
            result = st.session_state.search_result
            if "error" not in result and result.get('totalResultsCount', 0) > 0:
                record = result['geonames'][0]
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📍 Location Details")
                    st.write(f"**Postal Code:** {record['postalCode']}")
                    st.write(f"**City:** {record['placeName']}")
                    st.write(f"**State:** {record['state']}")
                    st.write(f"**Country:** {record['countryCode']}")
                    st.write(f"**Coordinates:** {record['lat']:.6f}, {record['lng']:.6f}")
                
                with col2:
                    st.subheader("🗺️ Map")
                    m = folium.Map(location=[record['lat'], record['lng']], zoom_start=12)
                    folium.Marker(
                        [record['lat'], record['lng']],
                        popup=f"{record['placeName']}, {record['state']} {record['postalCode']}",
                        tooltip=f"ZIP {record['postalCode']}"
                    ).add_to(m)
                    st_folium(m, height=300, width=400)
                
                st.json(result)
            else:
                st.warning("No results found for this postal code.")
    
    else:  # Prefix Search
        prefix = st.text_input("Enter postal code prefix:", placeholder="e.g., 737")
        max_results = st.slider("Maximum results:", 1, 50, 10)
        
        if st.button("Search by Prefix", type="primary") and prefix:
            with st.spinner("Searching..."):
                result = run_async(call_mcp_tool("postal_code_search", {"postal_code": prefix}))
                st.session_state.prefix_result = result
                st.session_state.search_prefix = prefix
        
        # Display prefix results from session state
        if hasattr(st.session_state, 'prefix_result'):
            result = st.session_state.prefix_result
            if "error" not in result and result.get('totalResultsCount', 0) > 0:
                st.success(f"Found {result['totalResultsCount']} postal codes starting with '{prefix}'")
                
                # Create DataFrame
                df = pd.DataFrame(result['geonames'])
                st.dataframe(df, use_container_width=True)
                
                # Show map if results exist
                if len(df) > 0:
                    st.subheader("🗺️ Map View")
                    fig = px.scatter_mapbox(
                        df, 
                        lat="lat", 
                        lon="lng",
                        hover_data=["postalCode", "placeName", "state"],
                        zoom=6,
                        height=500,
                        mapbox_style="open-street-map"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No results found for this prefix.")

# Geocode Postal Code
elif selected_tool == "🌍 Geocode Postal Code":
    st.header("🌍 Geocode Postal Code")
    st.markdown("Convert a postal code to geographic coordinates.")
    
    postal_code = st.text_input("Enter postal code:", placeholder="e.g., 90210")
    style = st.selectbox("Response Style:", ["SHORT", "MEDIUM", "LONG", "FULL"])
    
    if st.button("Geocode", type="primary") and postal_code:
        with st.spinner("Geocoding..."):
            tool_args = {"postalCode": postal_code}
            if style != "MEDIUM":
                tool_args["style"] = style
            result = run_async(call_mcp_tool("geocode_postal", tool_args))
            st.session_state.geocode_result = result
            st.session_state.geocode_postal_code = postal_code
    
    # Display geocode results from session state
    if hasattr(st.session_state, 'geocode_result'):
        result = st.session_state.geocode_result
        if "error" not in result and result.get('totalResultsCount', 0) > 0:
            record = result['geonames'][0]
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📍 Geocoding Result")
                st.metric("Latitude", f"{record['lat']:.6f}")
                st.metric("Longitude", f"{record['lng']:.6f}")
                st.write(f"**Location:** {record['placeName']}, {record['state']}")
                
                # Copy coordinates button
                coords_text = f"{record['lat']:.6f}, {record['lng']:.6f}"
                st.code(coords_text, language="text")
            
            with col2:
                st.subheader("🗺️ Location Map")
                m = folium.Map(location=[record['lat'], record['lng']], zoom_start=10)
                folium.Marker(
                    [record['lat'], record['lng']],
                    popup=f"{record['placeName']}, {record['state']} {record['postalCode']}",
                    tooltip=f"ZIP {record['postalCode']}"
                ).add_to(m)
                st_folium(m, height=300, width=400)
            
            st.json(result)
        else:
            st.error("Postal code not found or invalid.")

# Reverse Geocoding
elif selected_tool == "📍 Reverse Geocoding":
    st.header("📍 Reverse Geocoding")
    st.markdown("Find postal codes near geographic coordinates.")
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude:", value=47.606, format="%.6f", step=0.000001)
        radius = st.slider("Search Radius (km):", 1.0, 50.0, 5.0, 0.1)
    with col2:
        longitude = st.number_input("Longitude:", value=-122.332, format="%.6f", step=0.000001)
        max_results = st.slider("Maximum Results:", 1, 20, 10)
    
    # Quick location buttons
    st.markdown("**Quick Locations:**")
    location_cols = st.columns(4)
    
    with location_cols[0]:
        if st.button("Seattle, WA"):
            st.session_state.quick_lat = 47.606
            st.session_state.quick_lng = -122.332
    with location_cols[1]:
        if st.button("New York, NY"):
            st.session_state.quick_lat = 40.7128
            st.session_state.quick_lng = -74.0060
    with location_cols[2]:
        if st.button("Los Angeles, CA"):
            st.session_state.quick_lat = 34.0522
            st.session_state.quick_lng = -118.2437
    with location_cols[3]:
        if st.button("Chicago, IL"):
            st.session_state.quick_lat = 41.8781
            st.session_state.quick_lng = -87.6298
    
    # Update coordinates if quick location was selected
    if hasattr(st.session_state, 'quick_lat'):
        latitude = st.session_state.quick_lat
        longitude = st.session_state.quick_lng
        del st.session_state.quick_lat
        del st.session_state.quick_lng
    
    if st.button("Find Nearby Postal Codes", type="primary"):
        with st.spinner("Searching nearby postal codes..."):
            result = run_async(call_mcp_tool("reverse_geocode", {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius,
                "maxResults": max_results
            }))
            st.session_state.reverse_result = result
            st.session_state.reverse_coords = (latitude, longitude, radius)
    
    # Display reverse geocode results from session state
    if hasattr(st.session_state, 'reverse_result'):
        result = st.session_state.reverse_result
        if "error" not in result and result.get('totalResultsCount', 0) > 0:
            st.success(f"Found {result['totalResultsCount']} postal codes within {radius}km")
            
            # Create DataFrame
            df = pd.DataFrame(result['geonames'])
            df['distance_miles'] = df['distance'] * 0.621371  # Convert km to miles
            
            # Display results table
            st.subheader("📋 Nearby Postal Codes")
            display_df = df[['postalCode', 'placeName', 'state', 'distance', 'distance_miles']].copy()
            display_df.columns = ['ZIP Code', 'City', 'State', 'Distance (km)', 'Distance (mi)']
            st.dataframe(display_df, use_container_width=True)
            
            # Map visualization
            st.subheader("🗺️ Map View")
            m = folium.Map(location=[latitude, longitude], zoom_start=10)
            
            # Add search center
            folium.Marker(
                [latitude, longitude],
                popup="Search Center",
                tooltip="Your Search Location",
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)
            
            # Add postal code markers
            for _, row in df.iterrows():
                folium.Marker(
                    [row['lat'], row['lng']],
                    popup=f"{row['placeName']}, {row['state']} {row['postalCode']}<br>Distance: {row['distance']:.2f} km",
                    tooltip=f"ZIP {row['postalCode']} ({row['distance']:.2f} km)"
                ).add_to(m)
            
            # Add search radius circle
            folium.Circle(
                location=[latitude, longitude],
                radius=radius * 1000,  # Convert km to meters
                color='blue',
                fill=True,
                fillOpacity=0.1
            ).add_to(m)
            
            st_folium(m, height=500, width=700)
            
            st.json(result)
        else:
            st.warning("No postal codes found in the specified area.")

# Validate Postal Code
elif selected_tool == "✅ Validate Postal Code":
    st.header("✅ Validate Postal Code")
    st.markdown("Check if a postal code exists in the database.")
    
    postal_code = st.text_input("Enter postal code to validate:", placeholder="e.g., 12345")
    
    if st.button("Validate", type="primary") and postal_code:
        with st.spinner("Validating..."):
            result = run_async(call_mcp_tool("validate_postal", {"postalCode": postal_code}))
            st.session_state.validate_result = result
            st.session_state.validate_postal_code = postal_code
    
    # Display validation results from session state
    if hasattr(st.session_state, 'validate_result'):
        result = st.session_state.validate_result
        if "error" not in result:
            if result.get('valid', False):
                st.success(f"✅ Postal code {postal_code} is **VALID**")
                st.balloons()
            else:
                st.error(f"❌ Postal code {postal_code} is **INVALID** or not found in database")
            
            st.json(result)
        else:
            st.error(f"Error: {result['error']}")

# Footer
st.markdown("---")
st.markdown("""
### About This Demo
- **Database**: 33,791 US postal codes from Census Bureau ZCTA data
- **Technology**: Model Context Protocol (MCP) server with FastMCP
- **Performance**: Sub-millisecond exact lookups, <50ms reverse geocoding
- **Source Code**: [GitHub Repository](https://github.com/example/mcp-postal-geocoder)
""")