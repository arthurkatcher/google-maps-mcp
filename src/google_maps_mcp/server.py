"""MCP server with HTTP transport and API key authentication."""

import hmac
import os
from typing import Optional
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount
from mcp.server.fastmcp import FastMCP
import contextlib
from google_maps_mcp.tools import GoogleMapsTools


# Initialize FastMCP server
mcp = FastMCP("Google Maps MCP Server", stateless_http=True)
# Set MCP endpoint to root of mount path
mcp.settings.streamable_http_path = "/"

# Initialize tools
tools = GoogleMapsTools()


# Register the search_places tool
@mcp.tool()
async def search_places(
    query: str,
    max_results: int = 10
) -> dict:
    """Search Google Maps for places based on a text query.
    
    This tool searches for businesses, locations, and points of interest
    using Google Maps Places API. It returns detailed information including
    contact details, ratings, opening hours, and location data.
    
    Args:
        query: Search query like "coffee in San Francisco" or
               "pizza restaurants in New York City". Can include location
               and business type.
        max_results: Number of results to return (1-20). Default is 10.
    
    Returns:
        Dictionary containing query, total_results, and places list with
        detailed information including name, address, phone, website, rating,
        location, hours, and more.
    """
    return await tools.search_places(query, max_results)


@mcp.tool()
async def get_place_details(place_id: str) -> dict:
    """Get detailed information about a specific place by its Google Place ID.
    
    Use this to get more details about a place after finding it with search_places.
    Returns additional info like reviews, amenities, and editorial summaries.
    
    Args:
        place_id: Google Place ID (e.g., "places/ChIJN1t_tDeuEmsRUsoyG83frY4")
    
    Returns:
        Dictionary with detailed place information including:
        - Basic info: name, address, phone, website, rating
        - Reviews: Top 5 user reviews with ratings and text
        - Amenities: delivery, dine_in, takeout, outdoor_seating, etc.
        - Opening hours and business status
    """
    return await tools.get_place_details(place_id)


@mcp.tool()
async def search_nearby(
    latitude: float,
    longitude: float,
    radius_meters: int = 1000,
    place_type: str = None,
    max_results: int = 10
) -> dict:
    """Search for places near specific coordinates.
    
    Use this when you have GPS coordinates and want to find places nearby.
    Great for "find restaurants near me" type queries.
    
    Args:
        latitude: Latitude of the center point (e.g., 42.4531)
        longitude: Longitude of the center point (e.g., 18.5375)
        radius_meters: Search radius in meters (default 1000, max 50000)
        place_type: Optional type filter like "restaurant", "cafe", "hotel",
                   "gas_station", "pharmacy", "hospital", etc.
        max_results: Number of results to return (1-20). Default 10.
    
    Returns:
        Dictionary with center point, radius, and list of nearby places.
    
    Example:
        search_nearby(42.4531, 18.5375, radius_meters=500, place_type="cafe")
    """
    return await tools.search_nearby(
        latitude, longitude, radius_meters, place_type, max_results
    )


@mcp.tool()
async def get_directions(
    origin: str,
    destination: str,
    mode: str = "driving"
) -> dict:
    """Get directions and route between two locations.
    
    Returns step-by-step directions with distance and duration.
    Note: Requires Directions API to be enabled in Google Cloud.
    
    Args:
        origin: Starting point - can be address or "lat,lng" coordinates
        destination: End point - can be address or "lat,lng" coordinates  
        mode: Travel mode - "driving" (default), "walking", "bicycling", or "transit"
    
    Returns:
        Dictionary with route information including:
        - Total distance and duration
        - Step-by-step navigation instructions
        - Traffic duration (for driving)
        - Route warnings
    
    Example:
        get_directions("Union Square, San Francisco", "Ferry Building, San Francisco", mode="walking")
    """
    return await tools.get_directions(origin, destination, mode)


@mcp.tool()
async def geocode(address: str) -> dict:
    """Convert an address or place description to GPS coordinates.
    
    Use this when a user describes their location (hotel name, landmark, 
    street address) and you need coordinates for search_nearby.
    
    Args:
        address: Address, place name, landmark, or location description.
                Examples: "Ferry Building San Francisco", "Eiffel Tower Paris",
                "Times Square New York"
    
    Returns:
        Dictionary with:
        - formatted_address: The official address Google matched
        - latitude: Latitude coordinate
        - longitude: Longitude coordinate  
        - place_id: Google Place ID
    
    Example:
        geocode("Ferry Building, San Francisco")
    """
    return await tools.geocode(address)


@mcp.tool()
async def reverse_geocode(latitude: float, longitude: float) -> dict:
    """Convert GPS coordinates to a human-readable address.
    
    Use this when you have coordinates and need to know the address.
    
    Args:
        latitude: Latitude coordinate (e.g., 42.4531)
        longitude: Longitude coordinate (e.g., 18.5375)
    
    Returns:
        Dictionary with formatted address and location details.
    
    Example:
        reverse_geocode(42.4531, 18.5375)
    """
    return await tools.reverse_geocode(latitude, longitude)


# API Key authentication middleware
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate requests using X-API-Key header."""
    
    async def dispatch(self, request, call_next):
        # Skip auth for health check
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        expected_key = os.getenv("MCP_API_KEY")
        
        if not expected_key:
            # If no MCP_API_KEY is set, allow all requests (development mode)
            return await call_next(request)
        
        if not api_key or not hmac.compare_digest(api_key, expected_key):
            return JSONResponse(
                {"error": "Invalid or missing API key. Provide X-API-Key header."},
                status_code=401
            )
        
        return await call_next(request)


# Health check endpoint
async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "Google Maps MCP Server",
        "version": "0.1.0"
    })


def create_app() -> Starlette:
    """Create and configure the Starlette application."""
    
    # Create lifespan context for MCP session manager
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield
    
    # Get the MCP HTTP app
    mcp_app = mcp.streamable_http_app()
    
    # Create Starlette app with MCP mounted at /mcp
    app = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/", health_check, methods=["GET"]),
            Mount("/mcp", app=mcp_app),
        ],
        middleware=[
            Middleware(APIKeyMiddleware),
        ],
        lifespan=lifespan,
    )
    
    return app


async def cleanup():
    """Cleanup resources on shutdown."""
    await tools.close()


if __name__ == "__main__":
    # For development - can also use uvicorn directly
    import uvicorn
    from dotenv import load_dotenv
    
    load_dotenv()
    
    app = create_app()
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)

