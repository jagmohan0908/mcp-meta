"""MCP server configuration for self-hosted Meta Ads API."""

import argparse
import os
import sys

from mcp.server.fastmcp import FastMCP

from .auth import login as login_auth, meta_config
from .resources import get_resource, list_resources
from .utils import logger

# Initialize FastMCP server
mcp_server = FastMCP("meta-ads")

# Register resource URIs
mcp_server.resource(uri="meta-ads://resources")(list_resources)
mcp_server.resource(uri="meta-ads://images/{resource_id}")(get_resource)


def login_cli():
    """
    Command-line function to authenticate with Meta
    """
    logger.info("Starting Meta Ads CLI authentication flow")
    print("Starting Meta Ads CLI authentication flow...")
    
    # Call the common login function
    login_auth()


def main():
    """Main entry point for the package"""
    # Log startup information
    logger.info("Meta Ads MCP server starting")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Args: {sys.argv}")
    
    # Initialize argument parser
    parser = argparse.ArgumentParser(
        description="Meta Ads MCP Server - Model Context Protocol server for Meta Ads API",
        epilog="For more information, see https://github.com/pipeboard-co/meta-ads-mcp"
    )
    parser.add_argument("--login", action="store_true", help="Authenticate with Meta and store the token")
    parser.add_argument("--app-id", type=str, help="Meta App ID (Client ID) for authentication")
    parser.add_argument("--version", action="store_true", help="Show the version of the package")
    
    # Transport configuration arguments
    parser.add_argument("--transport", type=str, choices=["stdio", "streamable-http"], 
                       default="stdio", 
                       help="Transport method: 'stdio' for MCP clients (default), 'streamable-http' for HTTP API access")
    parser.add_argument("--port", type=int, default=8080, 
                       help="Port for Streamable HTTP transport (default: 8080, only used with --transport streamable-http)")
    parser.add_argument("--host", type=str, default="localhost", 
                       help="Host for Streamable HTTP transport (default: localhost, only used with --transport streamable-http)")
    parser.add_argument("--sse-response", action="store_true",
                       help="Use SSE response format instead of JSON (default: JSON, only used with --transport streamable-http)")
    parser.add_argument("--db-path", type=str, help="SQLite DB path for tenant/token store")
    args = parser.parse_args()
    logger.debug(f"Parsed args: login={args.login}, app_id={args.app_id}, version={args.version}")
    logger.debug(f"Transport args: transport={args.transport}, port={args.port}, host={args.host}, sse_response={args.sse_response}")
    
    # Validate CLI argument combinations
    if args.transport == "stdio" and (args.port != 8080 or args.host != "localhost" or args.sse_response):
        logger.warning("HTTP transport arguments (--port, --host, --sse-response) are ignored when using stdio transport")
        print("Warning: HTTP transport arguments are ignored when using stdio transport")
    
    from .auth import auth_manager
    env_app_id = os.environ.get("META_APP_ID")
    if args.app_id:
        logger.info("Setting app_id from command line")
        auth_manager.app_id = args.app_id
        meta_config.set_app_id(args.app_id)
    elif env_app_id:
        logger.info("Setting app_id from environment")
        auth_manager.app_id = env_app_id
        meta_config.set_app_id(env_app_id)
    if args.db_path:
        os.environ["META_MCP_DB_PATH"] = args.db_path
    
    # Show version if requested
    if args.version:
        from meta_ads_mcp import __version__
        logger.info(f"Displaying version: {__version__}")
        print(f"Meta Ads MCP v{__version__}")
        return 0
    
    # Handle login command
    if args.login:
        login_cli()
        return 0
    
    if not os.environ.get("META_MCP_ENCRYPTION_KEY"):
        print("Warning: META_MCP_ENCRYPTION_KEY is not set. Server may fail to start.")
    
    # Transport-specific server initialization and startup
    if args.transport == "streamable-http":
        logger.info(f"Starting MCP server with Streamable HTTP transport on {args.host}:{args.port}")
        logger.info("Mode: Stateless (no session persistence)")
        logger.info(f"Response format: {'SSE' if args.sse_response else 'JSON'}")
        print("Starting Meta Ads MCP server with Streamable HTTP transport")
        print(f"Server will listen on {args.host}:{args.port}")
        print(f"Response format: {'SSE' if args.sse_response else 'JSON'}")
        print("Authentication: Bearer <token> and X-TENANT-ID / X-TENANT-API-KEY headers")
        
        # Configure the existing server with streamable HTTP settings
        mcp_server.settings.host = args.host
        mcp_server.settings.port = args.port
        mcp_server.settings.stateless_http = True
        mcp_server.settings.json_response = not args.sse_response
        
        # Import all tool modules to ensure they are registered
        logger.info("Ensuring all tools are registered for HTTP transport")
        from . import accounts, campaigns, adsets, ads, insights, authentication
        from . import ads_library, budget_schedules, reports, openai_deep_research
        
        logger.info("Setting up HTTP authentication middleware")
        try:
            from .http_auth_integration import setup_fastmcp_http_auth
            setup_fastmcp_http_auth(mcp_server)
            print("Enabled tenant-aware HTTP authentication middleware")
        except Exception as e:
            logger.error("Failed to setup HTTP authentication integration: %s", e)
            print(f"Warning: HTTP authentication integration setup failed: {e}")

        try:
            print("Server configured successfully")
            mcp_server.run(transport="streamable-http")
        except Exception as e:
            logger.error(f"Error starting Streamable HTTP server: {e}")
            print(f"Error: Failed to start Streamable HTTP server: {e}")
            return 1
    else:
        # Default stdio transport
        logger.info("Starting MCP server with stdio transport")
        mcp_server.run(transport='stdio') 