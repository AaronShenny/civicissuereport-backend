import json
from datetime import datetime, timezone
from apps.users.models import AuditLog, Profile
from django.db import transaction

def _clean_dict(d: dict) -> dict:
    """Ensure dict doesn't contain sensitive fields."""
    if not isinstance(d, dict):
        return d
    sensitive_keys = {'password', 'token', 'jwt', 'secret', 'key'}
    return {
        k: v for k, v in d.items() 
        if not any(sk in k.lower() for sk in sensitive_keys)
    }

def log_audit_event(
    actor: Profile,
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value: dict = None,
    new_value: dict = None
) -> None:
    """
    Creates an immutable audit record in public.audit_logs.
    Only stores the fields that actually changed (diff) if old_value and new_value are provided.
    Never stores sensitive fields.
    """
    
    clean_old = _clean_dict(old_value) or {}
    clean_new = _clean_dict(new_value) or {}
    
    final_old = None
    final_new = None

    # Calculate diff
    if clean_old and clean_new:
        final_old = {}
        final_new = {}
        for k, v in clean_new.items():
            if k not in clean_old or clean_old[k] != v:
                final_new[k] = v
                if k in clean_old:
                    final_old[k] = clean_old[k]
    else:
        # If one is missing (e.g. creation or deletion), just use as is
        final_old = clean_old if clean_old else None
        final_new = clean_new if clean_new else None
        
    # Skip logging if there is no actual change and we expected one
    if clean_old and clean_new and not final_new and not final_old:
        return

    # Create audit record
    AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        old_value=final_old,
        new_value=final_new,
        # created_at is auto_now_add
    )
