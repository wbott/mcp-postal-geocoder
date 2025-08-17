#!/usr/bin/env python3
"""
Standalone MCP server bootstrap script for environments where package isn't installed.
This script ensures proper path setup before importing the main server.
"""

import sys
import os

print("=== MCP SERVER BOOTSTRAP STARTING ===")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print(f"Original sys.path: {sys.path}")

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Script directory: {script_dir}")

# Add src directory to Python path
src_dir = os.path.join(script_dir, "src")
if os.path.exists(src_dir):
    print(f"Found src directory: {src_dir}")
    print(f"Contents: {os.listdir(src_dir)}")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"Added {src_dir} to sys.path")
else:
    print(f"src directory not found at: {src_dir}")

print(f"Updated sys.path: {sys.path}")

# Now execute the MCP server directly
try:
    print("Attempting to execute MCP server...")
    server_file = os.path.join(src_dir, "mcp_postal_geocoder", "server", "mcp_server.py")
    print(f"Server file path: {server_file}")
    print(f"Server file exists: {os.path.exists(server_file)}")
    
    # Execute the server file directly
    with open(server_file, 'r') as f:
        server_code = f.read()
    
    print("Executing server code...")
    exec(server_code, {'__name__': '__main__', '__file__': server_file})
    
except Exception as e:
    print(f"Error executing MCP server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)