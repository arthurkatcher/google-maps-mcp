"""Google Maps Places API client."""

import os
import re
from typing import Optional
import httpx


_PLACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class GoogleMapsClient:
    """Client for Google Places API (New)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key.
        
        Args:
            api_key: Google Maps API key. If not provided, reads from GOOGLE_MAPS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Set GOOGLE_MAPS_API_KEY env var or pass api_key.")
        
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_places(
        self,
        query: str,
        max_results: int = 10
    ) -> dict:
        """Search for places using Google Places API Text Search.
        
        Args:
            query: Search query like "coffee in San Francisco"
            max_results: Number of results to return (1-20). Default 10.
        
        Returns:
            Dictionary with query, total_results, and places list.
        """
        # API max is 20 per request
        max_results = min(max_results, 20)
        
        # Field mask - request only the fields we need
        field_mask = [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.nationalPhoneNumber",
            "places.internationalPhoneNumber",
            "places.websiteUri",
            "places.googleMapsUri",
            "places.rating",
            "places.userRatingCount",
            "places.priceLevel",
            "places.regularOpeningHours",
            "places.businessStatus",
            "places.types",
            "places.location",
        ]
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(field_mask),
        }
        
        body = {
            "textQuery": query,
            "maxResultCount": max_results,
            "languageCode": "en",
        }
        
        try:
            response = await self.client.post(
                self.base_url,
                headers=headers,
                json=body
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Google Maps API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        # Transform to clean format
        places = []
        for place_data in data.get("places", []):
            place = {
                "place_id": place_data.get("id"),
                "name": place_data.get("displayName", {}).get("text", ""),
                "address": place_data.get("formattedAddress", ""),
                
                # Contact info
                "phone": place_data.get("internationalPhoneNumber") or place_data.get("nationalPhoneNumber"),
                "phone_local": place_data.get("nationalPhoneNumber"),
                "website": place_data.get("websiteUri"),
                "google_maps_url": place_data.get("googleMapsUri"),
                
                # Business info
                "rating": place_data.get("rating"),
                "reviews_count": place_data.get("userRatingCount"),
                "price_level": place_data.get("priceLevel"),
                "business_status": place_data.get("businessStatus"),
                "types": place_data.get("types", []),
                
                # Location
                "latitude": place_data.get("location", {}).get("latitude"),
                "longitude": place_data.get("location", {}).get("longitude"),
                
                # Hours
                "is_open_now": place_data.get("regularOpeningHours", {}).get("openNow"),
                "opening_hours": place_data.get("regularOpeningHours", {}).get("weekdayDescriptions"),
            }
            places.append(place)
        
        return {
            "query": query,
            "total_results": len(places),
            "places": places,
        }
    
    async def get_place_details(self, place_id: str) -> dict:
        """Get detailed information about a specific place.

        Args:
            place_id: Google Place ID (e.g., "ChIJN1t_tDeuEmsRUsoyG83frY4").
                     Accepts the bare ID or the "places/<id>" form returned by
                     the Places API; both are validated to alphanumerics,
                     underscore, and hyphen only.

        Returns:
            Dictionary with detailed place information.
        """
        if place_id.startswith("places/"):
            place_id = place_id[len("places/"):]
        if not _PLACE_ID_PATTERN.match(place_id):
            raise ValueError(
                f"Invalid place_id format: {place_id!r}. Expected "
                f"alphanumerics, underscore, or hyphen only."
            )
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        
        field_mask = [
            "id",
            "displayName",
            "formattedAddress",
            "nationalPhoneNumber",
            "internationalPhoneNumber",
            "websiteUri",
            "googleMapsUri",
            "rating",
            "userRatingCount",
            "priceLevel",
            "regularOpeningHours",
            "businessStatus",
            "types",
            "location",
            "reviews",
            "editorialSummary",
            "delivery",
            "dineIn",
            "takeout",
            "reservable",
            "servesBreakfast",
            "servesLunch",
            "servesDinner",
            "servesBeer",
            "servesWine",
            "servesBrunch",
            "servesVegetarianFood",
            "outdoorSeating",
            "liveMusic",
            "paymentOptions",
            "accessibilityOptions",
        ]
        
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(field_mask),
        }
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Google Maps API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        # Extract reviews
        reviews = []
        for review in data.get("reviews", [])[:5]:  # Limit to top 5 reviews
            reviews.append({
                "author": review.get("authorAttribution", {}).get("displayName"),
                "rating": review.get("rating"),
                "text": review.get("text", {}).get("text", ""),
                "time": review.get("relativePublishTimeDescription"),
            })
        
        return {
            "place_id": data.get("id"),
            "name": data.get("displayName", {}).get("text", ""),
            "address": data.get("formattedAddress", ""),
            "phone": data.get("internationalPhoneNumber") or data.get("nationalPhoneNumber"),
            "website": data.get("websiteUri"),
            "google_maps_url": data.get("googleMapsUri"),
            "rating": data.get("rating"),
            "reviews_count": data.get("userRatingCount"),
            "price_level": data.get("priceLevel"),
            "business_status": data.get("businessStatus"),
            "types": data.get("types", []),
            "latitude": data.get("location", {}).get("latitude"),
            "longitude": data.get("location", {}).get("longitude"),
            "is_open_now": data.get("regularOpeningHours", {}).get("openNow"),
            "opening_hours": data.get("regularOpeningHours", {}).get("weekdayDescriptions"),
            "editorial_summary": data.get("editorialSummary", {}).get("text"),
            "reviews": reviews,
            # Amenities
            "delivery": data.get("delivery"),
            "dine_in": data.get("dineIn"),
            "takeout": data.get("takeout"),
            "reservable": data.get("reservable"),
            "outdoor_seating": data.get("outdoorSeating"),
            "live_music": data.get("liveMusic"),
            "payment_options": data.get("paymentOptions"),
        }
    
    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 1000,
        place_type: str = None,
        max_results: int = 10
    ) -> dict:
        """Search for places near specific coordinates.
        
        Args:
            latitude: Latitude of the center point
            longitude: Longitude of the center point
            radius_meters: Search radius in meters (max 50000). Default 1000.
            place_type: Type of place to search for (e.g., "restaurant", "cafe", "hotel")
            max_results: Number of results to return (1-20). Default 10.
        
        Returns:
            Dictionary with query info and places list.
        """
        url = "https://places.googleapis.com/v1/places:searchNearby"
        max_results = min(max_results, 20)
        radius_meters = min(radius_meters, 50000)
        
        field_mask = [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.nationalPhoneNumber",
            "places.internationalPhoneNumber",
            "places.websiteUri",
            "places.googleMapsUri",
            "places.rating",
            "places.userRatingCount",
            "places.priceLevel",
            "places.regularOpeningHours",
            "places.businessStatus",
            "places.types",
            "places.location",
        ]
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(field_mask),
        }
        
        body = {
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": float(radius_meters)
                }
            },
            "maxResultCount": max_results,
            "languageCode": "en",
        }
        
        if place_type:
            body["includedTypes"] = [place_type]
        
        try:
            response = await self.client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Google Maps API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        places = []
        for place_data in data.get("places", []):
            place = {
                "place_id": place_data.get("id"),
                "name": place_data.get("displayName", {}).get("text", ""),
                "address": place_data.get("formattedAddress", ""),
                "phone": place_data.get("internationalPhoneNumber") or place_data.get("nationalPhoneNumber"),
                "website": place_data.get("websiteUri"),
                "google_maps_url": place_data.get("googleMapsUri"),
                "rating": place_data.get("rating"),
                "reviews_count": place_data.get("userRatingCount"),
                "price_level": place_data.get("priceLevel"),
                "business_status": place_data.get("businessStatus"),
                "types": place_data.get("types", []),
                "latitude": place_data.get("location", {}).get("latitude"),
                "longitude": place_data.get("location", {}).get("longitude"),
                "is_open_now": place_data.get("regularOpeningHours", {}).get("openNow"),
                "opening_hours": place_data.get("regularOpeningHours", {}).get("weekdayDescriptions"),
            }
            places.append(place)
        
        return {
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_meters": radius_meters,
            "place_type": place_type,
            "total_results": len(places),
            "places": places,
        }
    
    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> dict:
        """Get directions between two places.
        
        Note: Requires Directions API to be enabled.
        
        Args:
            origin: Starting point (address or "lat,lng")
            destination: Ending point (address or "lat,lng")
            mode: Travel mode - "driving", "walking", "bicycling", or "transit"
        
        Returns:
            Dictionary with route information.
        """
        url = "https://maps.googleapis.com/maps/api/directions/json"
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Directions API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        if data.get("status") != "OK":
            error_msg = data.get("error_message", data.get("status", "Unknown error"))
            raise Exception(f"Directions API error: {error_msg}")
        
        routes = []
        for route in data.get("routes", []):
            legs = []
            for leg in route.get("legs", []):
                steps = []
                for step in leg.get("steps", []):
                    steps.append({
                        "instruction": step.get("html_instructions", "").replace("<b>", "").replace("</b>", ""),
                        "distance": step.get("distance", {}).get("text"),
                        "duration": step.get("duration", {}).get("text"),
                        "travel_mode": step.get("travel_mode"),
                    })
                
                legs.append({
                    "start_address": leg.get("start_address"),
                    "end_address": leg.get("end_address"),
                    "distance": leg.get("distance", {}).get("text"),
                    "duration": leg.get("duration", {}).get("text"),
                    "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text"),
                    "steps": steps,
                })
            
            routes.append({
                "summary": route.get("summary"),
                "legs": legs,
                "warnings": route.get("warnings", []),
            })
        
        return {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "routes": routes,
        }
    
    async def geocode(self, address: str) -> dict:
        """Convert an address or place description to coordinates.
        
        Args:
            address: Address, place name, or location description
                    (e.g., "Eiffel Tower, Paris" or "123 Main St, NYC")
        
        Returns:
            Dictionary with formatted address and coordinates.
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            "address": address,
            "key": self.api_key,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Geocoding API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        if data.get("status") != "OK":
            error_msg = data.get("error_message", data.get("status", "No results found"))
            raise Exception(f"Geocoding error: {error_msg}")
        
        results = data.get("results", [])
        if not results:
            raise Exception("No location found for this address")
        
        # Get the best match (first result)
        result = results[0]
        location = result.get("geometry", {}).get("location", {})
        
        return {
            "query": address,
            "formatted_address": result.get("formatted_address"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
            "place_id": result.get("place_id"),
            "location_type": result.get("geometry", {}).get("location_type"),
            "types": result.get("types", []),
        }
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Convert coordinates to a human-readable address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        
        Returns:
            Dictionary with address information.
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.api_key,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Geocoding API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request failed: {str(e)}")
        
        if data.get("status") != "OK":
            error_msg = data.get("error_message", data.get("status", "No results found"))
            raise Exception(f"Reverse geocoding error: {error_msg}")
        
        results = data.get("results", [])
        if not results:
            raise Exception("No address found for these coordinates")
        
        # Get different address levels
        addresses = []
        for result in results[:3]:
            addresses.append({
                "formatted_address": result.get("formatted_address"),
                "types": result.get("types", []),
            })
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "formatted_address": results[0].get("formatted_address"),
            "place_id": results[0].get("place_id"),
            "address_components": addresses,
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

