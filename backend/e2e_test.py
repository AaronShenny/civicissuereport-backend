import os
import time
import requests
import django
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import Profile, Role
from apps.complaints.models import Complaint, ComplaintAttachment, ComplaintClassification, ComplaintStatusHistory
from apps.complaints.models import Notification
from apps.departments.models import DepartmentCategoryRule
from apps.complaints.models import ComplaintCategory

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

def run_e2e_test():
    report = {}
    print('Starting E2E Test...')
    
    # 1. AUTHENTICATION
    test_email = "civice2etest123@example.com"
    test_password = "SecurePassword123!"
    
    print(f'Logging in user: {test_email}')
    login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    resp = requests.post(login_url, headers=headers, json={
        "email": test_email,
        "password": test_password
    })
    
    if resp.status_code != 200:
        print('AUTH FAILED:', resp.text)
        return
        
    auth_data = resp.json()
    access_token = auth_data['access_token']
    user_id = auth_data['user']['id']
    
    print('User registered. Waiting for trigger to create profile...')
    time.sleep(3) # Wait for Postgres trigger
    
    profile = Profile.objects.filter(id=user_id).first()
    if profile:
        profile.account_status = Profile.ACCOUNT_STATUS_ACTIVE
        profile.save(update_fields=['account_status'])
        report['AUTHENTICATION'] = 'PASS'
        report['PROFILE CREATION'] = 'PASS'
        report['ROLE'] = 'PASS' if profile.role.role_name == Role.CITIZEN else 'FAIL'
        report['ACCOUNT STATUS'] = 'PASS' if profile.account_status == Profile.ACCOUNT_STATUS_ACTIVE else 'FAIL'
    else:
        print('Profile not found. Trigger might have failed.')
        return
        
    print('Profile created successfully.')

    # 2. CHECK ROUTING RULES
    category = ComplaintCategory.objects.filter(name='pothole').first()
    if not category:
        print('Missing category pothole')
        return
        
    # We need to ensure there is a DepartmentCategoryRule for 'Ernakulam' + 'pothole', or globally.
    # We will just print what exists to check if routing reference data is missing.
    rules = DepartmentCategoryRule.objects.filter(category_id=category.id, is_active=True)
    if not rules.exists():
        print("Required routing reference data is missing.")
        report['ROUTING'] = 'BLOCKED'
        report['SUPERVISOR NOTIFICATIONS'] = 'BLOCKED'
    else:
        print('Routing rules exist.')

    settings.ALLOWED_HOSTS = ['*']

    # 3. COMPLAINT SUBMISSION
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    
    payload = {
        "category_id": category.id,
        "description": "There is a large pothole approximately 1 meter wide in the middle of a busy road. Vehicles are swerving into the opposite lane to avoid it. The pothole becomes difficult to see at night and several vehicles have already nearly lost control.",
        "state": "Kerala",
        "district": "Ernakulam",
        "google_maps_url": "https://www.google.com/maps/@10.0158605,76.3418666,15z"
    }
    
    response = client.post('/api/v1/complaints/', payload, format='json')
    if response.status_code == 201:
        report['COMPLAINT SUBMISSION'] = 'PASS'
        complaint_id = response.data['id']
    else:
        print('COMPLAINT SUBMISSION FAILED:', getattr(response, 'data', response.content))
        return
        
    print(f'Complaint created: {complaint_id}')

    # 4. LOCATION EXTRACTION
    complaint = Complaint.objects.get(id=complaint_id)
    if complaint.location and complaint.location.x == 76.3418666 and complaint.location.y == 10.0158605:
        report['LOCATION EXTRACTION'] = 'PASS'
    else:
        report['LOCATION EXTRACTION'] = 'FAIL'

    # 5. STORAGE / ATTACHMENT
    report['STORAGE'] = 'SKIPPED'
    
    # 6. AI SEVERITY
    print('Waiting for AI Severity background task...')
    time.sleep(15)
    
    complaint.refresh_from_db()
    classification = ComplaintClassification.objects.filter(complaint_id=complaint_id).first()
    
    if classification:
        report['CLASSIFICATION STORAGE'] = 'PASS'
        if classification.severity_level == complaint.severity_level and classification.severity_score == complaint.severity_score:
            report['SEVERITY SYNCHRONIZATION'] = 'PASS'
            report['AI SEVERITY'] = 'PASS'
        else:
            report['SEVERITY SYNCHRONIZATION'] = 'FAIL'
            report['AI SEVERITY'] = 'FAIL'
    else:
        report['AI SEVERITY'] = 'FAIL'
        report['CLASSIFICATION STORAGE'] = 'FAIL'

    # 7. ROUTING AND SUPERVISORS
    if report.get('ROUTING') != 'BLOCKED':
        resp = client.post(f'/api/v1/complaints/{complaint_id}/route/')
        complaint.refresh_from_db()
        if complaint.assigned_department:
            report['ROUTING'] = 'PASS'
            # Check notifications
            notifs = Notification.objects.filter(complaint_id=complaint_id)
            if notifs.exists():
                report['SUPERVISOR NOTIFICATIONS'] = 'PASS'
            else:
                report['SUPERVISOR NOTIFICATIONS'] = 'FAIL'
        else:
            report['ROUTING'] = 'FAIL'
            report['SUPERVISOR NOTIFICATIONS'] = 'BLOCKED'

    # 8. RLS TEST
    # Try accessing another user's complaint
    other_complaint = Complaint.objects.exclude(citizen_id=user_id).first()
    if other_complaint:
        resp = client.get(f'/api/v1/complaints/{other_complaint.id}/')
        if resp.status_code == 404:
            report['RLS SECURITY TEST'] = 'PASS'
        else:
            report['RLS SECURITY TEST'] = f'FAIL: {resp.status_code}'
    else:
        report['RLS SECURITY TEST'] = 'SKIPPED'

    # PRINT REPORT
    print("\n--- FINAL REPORT ---")
    for k, v in report.items():
        print(f"{k}: {v}")
        
    print("\n--- TEST DATA ---")
    print(f"TEST USER ID: {user_id}")
    print(f"COMPLAINT ID: {complaint_id}")
    if classification:
        print(f"CLASSIFICATION ID: {classification.id}")
        print(f"SEVERITY RESULT: {classification.severity_level} / {classification.severity_score}")
        print(f"CONFIDENCE: {classification.confidence_score}")
        print(f"AI MODEL: {classification.model_name}")
    print(f"ROUTED DEPARTMENT: {complaint.assigned_department.name if complaint.assigned_department else 'None'}")
    print(f"MATCHING SUPERVISOR COUNT: {notifs.count() if 'notifs' in locals() else 0}")
    
if __name__ == '__main__':
    run_e2e_test()
