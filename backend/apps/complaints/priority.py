"""
apps/complaints/priority.py

Deterministic and Hybrid AI Priority Engine (Phase 11)
"""

from apps.complaints.models import PriorityCategory

def get_base_priority(category_name: str) -> str:
    """
    Returns the deterministic BASE priority for a given category name.
    """
    mapping = {
        'drainage': PriorityCategory.HIGH,
        'garbage': PriorityCategory.HIGH,
        'other': PriorityCategory.MEDIUM,
        'pothole': PriorityCategory.HIGH,
        'road_damage': PriorityCategory.HIGH,
        'sanitation': PriorityCategory.HIGH,
        'streetlight': PriorityCategory.MEDIUM,
        'water_supply': PriorityCategory.HIGH,
    }
    
    # Normalize category name for lookup
    normalized_name = category_name.strip().lower().replace(' ', '_')
    return mapping.get(normalized_name, PriorityCategory.MEDIUM)

def calculate_final_priority(base_priority: str, ai_severity_level: str = None) -> str:
    """
    Modifies the BASE priority using the AI severity level.
    
    AI = critical -> promote one priority tier
    AI = low      -> demote one priority tier
    AI = medium/high -> keep base priority
    """
    levels = [PriorityCategory.LOW, PriorityCategory.MEDIUM, PriorityCategory.HIGH]
    
    try:
        base_index = levels.index(base_priority)
    except ValueError:
        base_index = 1 # default to MEDIUM
        
    if not ai_severity_level:
        return base_priority
        
    normalized_ai = ai_severity_level.strip().lower()
    
    if normalized_ai == 'critical':
        final_index = min(len(levels) - 1, base_index + 1)
    elif normalized_ai == 'low':
        final_index = max(0, base_index - 1)
    else:
        # medium or high
        final_index = base_index
        
    return levels[final_index]
