#!/usr/bin/env python3
"""
Bootstrap script for MCP Postal Geocoder server.

This script is used in containerized environments (like Hugging Face Spaces)
where the package isn't installed. It sets up the Python path and executes
the main server directly.
"""

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Bootstrap the MCP server with proper path setup."""
    logger.info("Starting MCP Postal Geocoder server bootstrap")
    
    # Get script directory and add src to Python path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, "src")
    
    if not os.path.exists(src_dir):
        logger.error(f"Source directory not found: {src_dir}")
        sys.exit(1)
    
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        logger.info(f"Added {src_dir} to Python path")
    
    # Execute the MCP server
    try:
        server_file = os.path.join(src_dir, "mcp_postal_geocoder", "server", "mcp_server.py")
        
        if not os.path.exists(server_file):
            logger.error(f"Server file not found: {server_file}")
            sys.exit(1)
        
        logger.info("Executing MCP server")
        with open(server_file, 'r') as f:
            server_code = f.read()
        
        exec(server_code, {'__name__': '__main__', '__file__': server_file})
        
    except Exception as e:
        logger.error(f"Failed to execute MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()