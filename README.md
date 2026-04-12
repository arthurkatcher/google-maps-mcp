# Google Maps MCP Server

[![PyPI version](https://img.shields.io/pypi/v/google-maps-mcp.svg)](https://pypi.org/project/google-maps-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready [Model Context Protocol](https://modelcontextprotocol.io) server that gives AI agents **real Google Maps capabilities** — place search, directions, geocoding, and more. Works with Claude Desktop, Cursor, Claude Code, and any other MCP-compatible client. Supports both **stdio** (local) and **streamable HTTP** (remote) transports.

## What it does

Six tools, all hitting the real Google Maps APIs:

| Tool | What it does |
|---|---|
| `search_places` | Text search for places — "best ramen in Tokyo", "24h pharmacy near me" |
| `get_place_details` | Reviews, amenities, hours, phone, website, price level |
| `search_nearby` | Find places within a radius of specific coordinates, filter by type |
| `get_directions` | Step-by-step routes (driving, walking, bicycling, transit) |
| `geocode` | Address or landmark → GPS coordinates |
| `reverse_geocode` | GPS coordinates → human-readable address |

## Quick install — Claude Desktop

Add to your `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "uvx",
      "args": ["google-maps-mcp"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_google_maps_api_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. That's it — no cloning, no venv, no Docker. `uvx` fetches the package from PyPI on first run and caches it.

## Quick install — Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "uvx",
      "args": ["google-maps-mcp"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_google_maps_api_key_here"
      }
    }
  }
}
```

Restart Cursor.

## Quick install — Claude Code CLI

```bash
claude mcp add google-maps \
  -e GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here \
  -- uvx google-maps-mcp
```

## Get a Google Maps API key

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create (or pick) a project.
2. **Enable billing** on the project — yes, it's required even for the free tier. Google gives **$200/month in free Maps credit**, which is far more than most solo-use ever consumes.
3. Enable these APIs in **APIs & Services → Library**:
   - **Places API (New)** — for `search_places`, `get_place_details`, `search_nearby`
   - **Directions API** — for `get_directions`
   - **Geocoding API** — for `geocode`, `reverse_geocode`
4. Go to **APIs & Services → Credentials → + CREATE CREDENTIALS → API key**.
5. (Recommended) Restrict the key to just those four APIs.
6. Paste the key into your MCP config above.

## Try it

Once installed, in Claude Desktop / Cursor / Claude Code, ask things like:

- "Find specialty coffee shops near me in San Francisco"
- "How long does it take to walk from Union Square to the Ferry Building?"
- "What are the coordinates of the Eiffel Tower?"
- "What's the address at 37.8199, -122.4783?"
- "Show me the reviews for the top-rated ramen place in Shibuya"

The model picks the right tool automatically — you don't need to name it.

## Remote HTTP server mode

For deployment, shared usage, or A2A (agent-to-agent) scenarios, the same package also runs as a streamable HTTP server:

```bash
git clone https://github.com/arthurkatcher/google-maps-mcp
cd google-maps-mcp
uv sync
cp .env.example .env  # edit with your API key
python run.py
```

Server listens on `http://0.0.0.0:8000` with the MCP endpoint at `/mcp/` and a health check at `/health`. Set `MCP_API_KEY` in `.env` to require `X-API-Key` header authentication; leave it unset for dev mode.

To expose publicly:

```bash
ngrok http 8000
# then point clients at https://your-ngrok-url.ngrok-free.dev/mcp/
```

## Tool reference

### `search_places`

```python
search_places(
    query: str,           # "coffee in San Francisco"
    max_results: int = 10 # 1-20
)
```

Returns: `query`, `total_results`, `places` (list with `name`, `address`, `phone`, `website`, `rating`, `reviews_count`, `types`, `latitude`, `longitude`, `is_open_now`, `opening_hours`, `google_maps_url`, `price_level`, `business_status`).

### `get_place_details`

```python
get_place_details(
    place_id: str  # Google Place ID from a prior search
)
```

Returns everything from `search_places` plus: top 5 `reviews`, amenities (`delivery`, `dine_in`, `takeout`, `outdoor_seating`, `live_music`, `reservable`), `editorial_summary`, `payment_options`.

### `search_nearby`

```python
search_nearby(
    latitude: float,            # e.g. 37.7955
    longitude: float,           # e.g. -122.3937
    radius_meters: int = 1000,  # max 50000
    place_type: str = None,     # "restaurant", "cafe", "hotel", "gas_station", ...
    max_results: int = 10
)
```

### `get_directions`

```python
get_directions(
    origin: str,       # address, landmark, or "lat,lng"
    destination: str,  # same
    mode: str = "driving"  # "driving" | "walking" | "bicycling" | "transit"
)
```

Returns total distance and duration plus step-by-step instructions.

### `geocode` / `reverse_geocode`

```python
geocode(address: str)                                  # → lat/lng
reverse_geocode(latitude: float, longitude: float)     # → formatted address
```

## Pricing

Google's Maps Platform offers a **$200/month free credit** that covers:
- ~11,000 Places API (New) requests, or
- ~40,000 Geocoding API requests, or
- ~40,000 Directions API requests.

For solo or small-team use, you will almost never hit the cap. Past the free tier, expect ~$17 per 1000 Places requests and ~$5 per 1000 Geocoding/Directions requests. See [Google's pricing page](https://developers.google.com/maps/billing-and-pricing/pricing) for current rates.

## Development

```bash
git clone https://github.com/arthurkatcher/google-maps-mcp
cd google-maps-mcp
uv sync
cp .env.example .env  # add your API key

# Run stdio mode (for local MCP clients)
uv run python -m google_maps_mcp

# Run HTTP mode (for remote access)
uv run python run.py
```

## Project structure

```
google-maps-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── run.py                  # HTTP server entry point
└── src/google_maps_mcp/
    ├── __init__.py
    ├── __main__.py         # stdio server entry point
    ├── client.py           # Google Maps API client
    ├── tools.py            # Tool wrappers
    └── server.py           # FastMCP server + HTTP middleware
```

## License

MIT — see [LICENSE](LICENSE).

## Credits

Built by [Arthur Katcher](https://github.com/arthurkatcher) as part of the MCP ecosystem. PRs welcome.
