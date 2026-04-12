"""MCP tools for Google Maps search."""

from typing import Optional
from google_maps_mcp.client import GoogleMapsClient


class GoogleMapsTools:
    """MCP tools wrapper for Google Maps."""
    
    def __init__(self):
        """Initialize the tools with a Google Maps client."""
        self.client = GoogleMapsClient()
    
    async def search_places(
        self,
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
            Dictionary containing:
            - query: The original search query
            - total_results: Number of places found
            - places: List of place dictionaries with:
              - place_id: Unique Google Places ID
              - name: Business/place name
              - address: Full formatted address
              - phone: International phone number (if available)
              - phone_local: Local phone number (if available)
              - website: Website URL (if available)
              - google_maps_url: Direct link to Google Maps
              - rating: Average rating (0-5)
              - reviews_count: Number of reviews
              - price_level: Price level indicator
              - business_status: Operating status (OPERATIONAL, CLOSED_TEMPORARILY, etc.)
              - types: List of place types (e.g., ["cafe", "coffee_shop"])
              - latitude: Latitude coordinate
              - longitude: Longitude coordinate
              - is_open_now: Whether currently open (if hours available)
              - opening_hours: List of weekday hour descriptions
        
        Example:
            search_places("coffee in San Francisco", max_results=5)
        """
        return await self.client.search_places(query, max_results)
    
    async def get_place_details(self, place_id: str) -> dict:
        """Get detailed information about a specific place by its Google Place ID.
        
        Use this to get more details about a place after finding it with search_places.
        Returns additional info like reviews, amenities, and editorial summaries.
        
        Args:
            place_id: Google Place ID (starts with "places/" or just the ID)
        
        Returns:
            Dictionary with detailed place information including:
            - Basic info: name, address, phone, website, rating
            - Reviews: Top 5 user reviews with ratings and text
            - Amenities: delivery, dine_in, takeout, outdoor_seating, etc.
            - Opening hours and business status
        """
        return await self.client.get_place_details(place_id)
    
    async def search_nearby(
        self,
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
        return await self.client.search_nearby(
            latitude, longitude, radius_meters, place_type, max_results
        )
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> dict:
        """Get directions and route between two locations.
        
        Returns step-by-step directions with distance and duration.
        
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
        return await self.client.get_directions(origin, destination, mode)
    
    async def geocode(self, address: str) -> dict:
        """Convert an address or place description to coordinates.
        
        Use this when a user describes their location and you need coordinates
        for search_nearby or other location-based operations.
        
        Args:
            address: Address, place name, landmark, or location description.
                    Examples: "Ferry Building San Francisco", "Eiffel Tower Paris",
                    "Times Square New York", "123 Main St, New York"
        
        Returns:
            Dictionary with:
            - formatted_address: The official address Google found
            - latitude: Latitude coordinate
            - longitude: Longitude coordinate
            - place_id: Google Place ID for this location
        """
        return await self.client.geocode(address)
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Convert coordinates to a human-readable address.
        
        Use this when you have coordinates and need to know the address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        
        Returns:
            Dictionary with formatted address and location details.
        """
        return await self.client.reverse_geocode(latitude, longitude)
    
    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.close()

