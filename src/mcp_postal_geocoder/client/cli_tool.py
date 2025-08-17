"""Command-line interface for postal code geocoding using MCP client."""

import argparse
import asyncio
import json
import sys
import platform
from typing import Dict, Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


def get_python_command() -> str:
    """Get the appropriate Python command for the current platform."""
    if platform.system() == "Windows":
        return "python"
    else:
        return "python3"


async def test_mcp_server() -> None:
    """Test the MCP server functionality."""
    
    # Start the MCP server process
    server_params = StdioServerParameters(
        command=get_python_command(),
        args=["-m", "mcp_postal_geocoder.server.mcp_server"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                print("Available tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n" + "="*50)
                
                # Test postal_code_search
                print("\n1. Testing postal_code_search with ZIP 73717:")
                result = await session.call_tool("postal_code_search", {"postal_code": "73717"})
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
                
                # Test geocode_postal
                print("\n2. Testing geocode_postal with ZIP 90210:")
                result = await session.call_tool("geocode_postal", {"postalCode": "90210"})
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
                
                # Test reverse_geocode
                print("\n3. Testing reverse_geocode near Seattle:")
                result = await session.call_tool("reverse_geocode", {
                    "latitude": 47.606,
                    "longitude": -122.332,
                    "radius": 5.0,
                    "maxResults": 3
                })
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
                
                # Test validate_postal
                print("\n4. Testing validate_postal with ZIP 12345:")
                result = await session.call_tool("validate_postal", {"postalCode": "12345"})
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
                
                # Test postal_stats
                print("\n5. Testing postal_stats:")
                result = await session.call_tool("postal_stats", {})
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
    
    except Exception as e:
        print(f"Error testing MCP server: {e}")
        print(f"Server command: {get_python_command()} -m mcp_postal_geocoder.server.mcp_server")
        raise


async def run_cli_command(args) -> None:
    """Run CLI command using MCP client."""
    
    server_params = StdioServerParameters(
        command=get_python_command(),
        args=["-m", "mcp_postal_geocoder.server.mcp_server"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                if args.command == "search":
                    tool_args = {"postal_code": args.postal_code or args.prefix}
                    if args.style != "MEDIUM":
                        tool_args["style"] = args.style
                    result = await session.call_tool("postal_code_search", tool_args)
                    
                elif args.command == "geocode":
                    tool_args = {"postalCode": args.postal_code}
                    if args.style != "MEDIUM":
                        tool_args["style"] = args.style
                    result = await session.call_tool("geocode_postal", tool_args)
                    
                elif args.command == "reverse":
                    tool_args = {
                        "latitude": args.latitude,
                        "longitude": args.longitude,
                        "radius": args.radius,
                        "maxResults": args.max_results
                    }
                    if args.style != "MEDIUM":
                        tool_args["style"] = args.style
                    result = await session.call_tool("reverse_geocode", tool_args)
                    
                elif args.command == "validate":
                    result = await session.call_tool("validate_postal", {"postalCode": args.postal_code})
                    
                elif args.command == "stats":
                    result = await session.call_tool("postal_stats", {})
                    
                elif args.command == "test":
                    await test_mcp_server()
                    return
                
                else:
                    print(f"Unknown command: {args.command}")
                    return
                
                # Print result
                if result.content:
                    response = json.loads(result.content[0].text)
                    print(json.dumps(response, indent=2))
                else:
                    print("No response received")
    
    except Exception as e:
        print(f"Error running CLI command: {e}")
        print(f"Server command: {get_python_command()} -m mcp_postal_geocoder.server.mcp_server")
        raise


def main() -> None:
    """CLI entry point for postal geocoding operations."""
    parser = argparse.ArgumentParser(description="Postal Code Geocoding CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    subparsers.add_parser("test", help="Run comprehensive test of all tools")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search postal codes")
    search_parser.add_argument("--postal-code", help="Exact postal code")
    search_parser.add_argument("--prefix", help="Postal code prefix")
    search_parser.add_argument("--max-rows", type=int, default=10, help="Maximum results")
    search_parser.add_argument("--style", choices=["SHORT", "MEDIUM", "LONG", "FULL"], 
                              default="MEDIUM", help="Response style")
    
    # Geocode command
    geocode_parser = subparsers.add_parser("geocode", help="Geocode postal code")
    geocode_parser.add_argument("postal_code", help="Postal code to geocode")
    geocode_parser.add_argument("--style", choices=["SHORT", "MEDIUM", "LONG", "FULL"], 
                               default="MEDIUM", help="Response style")
    
    # Reverse geocode command
    reverse_parser = subparsers.add_parser("reverse", help="Reverse geocode coordinates")
    reverse_parser.add_argument("latitude", type=float, help="Latitude")
    reverse_parser.add_argument("longitude", type=float, help="Longitude")
    reverse_parser.add_argument("--radius", type=float, default=5.0, help="Search radius in km")
    reverse_parser.add_argument("--max-results", type=int, default=10, help="Maximum results")
    reverse_parser.add_argument("--style", choices=["SHORT", "MEDIUM", "LONG", "FULL"], 
                               default="MEDIUM", help="Response style")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate postal code")
    validate_parser.add_argument("postal_code", help="Postal code to validate")
    
    # Stats command
    subparsers.add_parser("stats", help="Database statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the async CLI command
    asyncio.run(run_cli_command(args))


if __name__ == "__main__":
    main()