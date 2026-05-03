"""Entry point to run the Google Maps MCP server."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from google_maps_mcp.server import create_app
import uvicorn


def main():
    """Start the MCP server."""
    # Validate required environment variables
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY environment variable is required.")
        print("Please set it in your .env file.")
        sys.exit(1)
    
    # Get configuration
    mcp_api_key = os.getenv("MCP_API_KEY")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))

    if not mcp_api_key:
        if host in ("127.0.0.1", "localhost", "::1"):
            print("INFO: MCP_API_KEY not set — server is loopback-only.")
        else:
            print(
                f"WARNING: MCP_API_KEY is not set and the server is binding "
                f"{host} (non-loopback). Anyone who can reach this host can "
                f"use your GOOGLE_MAPS_API_KEY and bill your Google Cloud "
                f"account. Set MCP_API_KEY=<random-string> in .env, or set "
                f"MCP_HOST=127.0.0.1.",
                file=sys.stderr,
            )
    
    print(f"Starting Google Maps MCP Server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  MCP Endpoint: http://{host}:{port}/mcp")
    print(f"  Health Check: http://{host}:{port}/health")
    
    if mcp_api_key:
        print(f"  Authentication: Enabled (X-API-Key header required)")
    else:
        print(f"  Authentication: Disabled (development mode)")
    
    # Create and run the app
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()


