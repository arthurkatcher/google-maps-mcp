"""Stdio entry point for google_maps_mcp.

Runs the MCP server over stdio transport — the standard local-process transport
used by Claude Desktop, Cursor, and other MCP clients. Use this for
`python -m google_maps_mcp` or as the console script `google-maps-mcp`.

For HTTP/network transport, use `python run.py` instead.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE importing server module — the server module instantiates
# GoogleMapsClient at import time, which requires GOOGLE_MAPS_API_KEY.
_project_root = Path(__file__).resolve().parent.parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def main() -> None:
    """Run the google_maps_mcp server over stdio."""
    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        print(
            "ERROR: GOOGLE_MAPS_API_KEY is required. "
            "Set it in .env or pass it via the env.",
            file=sys.stderr,
        )
        sys.exit(1)

    from google_maps_mcp.server import mcp

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
