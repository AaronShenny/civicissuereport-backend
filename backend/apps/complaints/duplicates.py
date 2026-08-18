import logging
from math import radians, cos, sin, asin, sqrt
from django.db import transaction
from apps.complaints.models import Complaint

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two points on the earth."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000 # Radius of earth in meters
    return c * r

def get_ultimate_main_complaint(complaint_id) -> Complaint | None:
    """
    Follows the chain of main_complaint_id to find the ultimate primary complaint.
    Prevents arbitrary duplicate chains (e.g. C -> B -> A will return A).
    """
    current = Complaint.objects.get(id=complaint_id)
    visited = set()
    while current.main_complaint_id:
        if current.id in visited:
            break
        visited.add(current.id)
        current = current.main_complaint
    return current

@transaction.atomic
def detect_and_link_duplicate(new_complaint: Complaint) -> bool:
    """
    Finds if the new_complaint is a duplicate of an existing active complaint.
    Rule: SAME CATEGORY AND SAME DISTRICT AND DISTANCE <= 10 METERS
    
    If so, sets its main_complaint_id to the ultimate primary complaint,
    increments primary's reporter_count, saves, and returns True.
    """
    if not new_complaint.category_id or not new_complaint.district:
        return False
        
    lat1 = float(new_complaint.location_lat)
    lon1 = float(new_complaint.location_lng)
    
    # Filter active complaints in same category and district
    candidates = Complaint.objects.filter(
        category_id=new_complaint.category_id,
        district__iexact=new_complaint.district
    ).exclude(
        id=new_complaint.id
    ).exclude(
        status__in=['resolved', 'closed', 'invalid']
    ).order_by('submitted_at')
    
    for candidate in candidates:
        lat2 = float(candidate.location_lat)
        lon2 = float(candidate.location_lng)
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        if distance <= 10.0:
            ultimate_primary = get_ultimate_main_complaint(candidate.id)
            
            # Lock the primary complaint for concurrency safety
            primary_locked = Complaint.objects.select_for_update().get(id=ultimate_primary.id)
            
            new_complaint.main_complaint = primary_locked
            new_complaint.save(update_fields=['main_complaint'])
            
            primary_locked.reporter_count += 1
            primary_locked.save(update_fields=['reporter_count'])
            
            logger.info("Complaint %s linked as duplicate to %s (distance %.2fm)", 
                        new_complaint.complaint_number, primary_locked.complaint_number, distance)
            return True
            
    return False
