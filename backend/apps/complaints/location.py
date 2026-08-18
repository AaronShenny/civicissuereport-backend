import re
import urllib.parse
import urllib.request
import logging

logger = logging.getLogger(__name__)

class LocationExtractionError(Exception):
    pass

def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    """
    Extracts latitude and longitude from a Google Maps URL or coordinate string.
    Follows redirects for shortened URLs (maps.app.goo.gl).
    Returns a tuple of (latitude, longitude) as floats.
    Raises LocationExtractionError if parsing fails or coordinates are invalid.
    """
    if not url:
        raise LocationExtractionError("URL cannot be empty")
    
    url = url.strip()

    # 5. Generic valid coordinate pairs
    coord_pair_pattern = r'^([-+]?(?:[1-8]?\d(?:\.\d+)?|90(?:\.0+)?))\s*,\s*([-+]?(?:180(?:\.0+)?|(?:1[0-7]\d|[1-9]?\d)(?:\.\d+)?))$'
    match = re.match(coord_pair_pattern, url)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
        return _validate_coords(lat, lng)

    # 1. maps.app.goo.gl short URLs (and other goo.gl links)
    if 'goo.gl' in url:
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=5) as response:
                url = response.url
        except Exception as e:
            logger.error(f"Failed to resolve short URL {url}: {e}")
            raise LocationExtractionError(f"Failed to resolve short URL: {e}")

    url = urllib.parse.unquote(url)

    # 4. Google Maps @LAT,LNG URLs
    # Pattern looks for @ followed by lat,lng
    at_pattern = r'@([-+]?\d{1,2}\.\d+),([-+]?\d{1,3}\.\d+)'
    match = re.search(at_pattern, url)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
        return _validate_coords(lat, lng)

    # 2. Google Maps place URLs containing !3dLAT!4dLNG
    place_pattern = r'!3d([-+]?\d{1,2}\.\d+)!4d([-+]?\d{1,3}\.\d+)'
    match = re.search(place_pattern, url)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
        return _validate_coords(lat, lng)

    # 3. Google Maps search URLs containing /maps/search/LAT,LNG or /maps/place/LAT,LNG
    search_pattern = r'/maps/(?:search|place)/([-+]?\d{1,2}\.\d+),([-+]?\d{1,3}\.\d+)'
    match = re.search(search_pattern, url)
    if match:
        lat, lng = float(match.group(1)), float(match.group(2))
        return _validate_coords(lat, lng)

    raise LocationExtractionError("Could not extract coordinates from the provided URL")

def _validate_coords(lat: float, lng: float) -> tuple[float, float]:
    if not (-90.0 <= lat <= 90.0):
        raise LocationExtractionError(f"Invalid latitude: {lat}")
    if not (-180.0 <= lng <= 180.0):
        raise LocationExtractionError(f"Invalid longitude: {lng}")
    return lat, lng
