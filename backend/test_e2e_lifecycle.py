import os
import sys
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from unittest.mock import patch
from apps.users.models import Profile, Role
from apps.complaints.models import Complaint, ComplaintCategory
from apps.departments.models import Department, DepartmentCategoryRule

def run_e2e():
    print("--- STARTING E2E API TRACE ---")

    print("1. Looking up Citizen...")
    citizen = Profile.objects.filter(role__role_name='citizen').first()
    if not citizen:
        print("No citizen found! Run the frontend and login once to create a citizen.")
        return
    citizen.account_status = 'active'
    citizen.save()

    print("2. Looking up Department/Category...")
    rule = DepartmentCategoryRule.objects.filter(is_active=True).select_related('category', 'department').first()
    if not rule:
        from django.utils import timezone
        now = timezone.now()
        cat = ComplaintCategory.objects.first()
        dept = Department.objects.first()
        if not cat or not dept:
            print("No category or department found to create a rule!")
            return
        rule = DepartmentCategoryRule.objects.create(
            id=uuid.uuid4(),
            category=cat, 
            department=dept, 
            is_active=True, 
            priority_rank=1, 
            created_at=now
        )
        print("Created new routing rule.")
    cat = rule.category
    dept = rule.department

    # Mock SupabaseAuth to return the citizen
    citizen.is_authenticated = True
    citizen.profile = citizen
    with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth:
        mock_auth.return_value = (citizen, None)

        client = Client()
        print("3. Submitting complaint via API...")
        res = client.post('/api/v1/complaints/', {
            'category_id': cat.id,
            'description': 'Pothole E2E test via API',
            'latitude': 12.345,
            'longitude': 67.890,
            'google_maps_url': 'https://www.google.com/maps/search/12.345,+67.890',
            'state': 'Kerala',
            'district': 'Ernakulam'
        })
        
        print(f"Status Code: {res.status_code}")
        if res.status_code != 201:
            print(f"Response: {res.content.decode()}")
            print("--- SUBMISSION FAILED ---")
            return

        complaint_id = res.json().get('id')
        print(f"Complaint created with ID: {complaint_id}")
        
        print("4. Triggering Routing via API...")
        res = client.post(f'/api/v1/complaints/{complaint_id}/route/')
        print(f"Routing Status: {res.status_code}")
        print(f"Routing Response: {res.content.decode()}")

        # We need the profiles of employee and supervisor
        supervisor = Profile.objects.filter(role__role_name='supervisor', department=dept).first()
        employee = Profile.objects.filter(role__role_name='ground_level_employee', department=dept).first()

        if not supervisor or not employee:
            print("Need to repurpose existing users to be supervisor/employee for E2E...")
            users = list(Profile.objects.exclude(id=citizen.id))
            if len(users) < 2:
                print("Not enough users in DB to repurpose. Need at least 3 users total.")
                return
            
            sup_role = Role.objects.get(role_name='supervisor')
            emp_role = Role.objects.get(role_name='ground_level_employee')
            
            supervisor = users[0]
            supervisor.role = sup_role
            supervisor.department = dept
            supervisor.account_status = 'active'
            supervisor.save()
            
            employee = users[1]
            employee.role = emp_role
            employee.department = dept
            employee.account_status = 'active'
            employee.save()
            
            print(f"Repurposed {supervisor.email} as supervisor and {employee.email} as employee.")

        if supervisor:
            supervisor.account_status = 'active'
            supervisor.save()
        if employee:
            employee.account_status = 'active'
            employee.save()
            
        print("5. Assigning Employee via API (Supervisor)...")
        # Mock Auth as supervisor
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth_sup:
            supervisor.is_authenticated = True
            supervisor.profile = supervisor
            mock_auth_sup.return_value = (supervisor, 'dummy_token')
            
            res = client.post(f'/api/v1/supervisor/complaints/{complaint_id}/assign/', {
                'employee_id': str(employee.id),
                'assignment_reason': 'E2E Testing'
            })
            print(f"Assignment Status: {res.status_code}")
            if res.status_code != 200:
                print(f"Response: {res.content.decode()}")
                return
            
        print("6. Verifying Complaint via API (Employee)...")
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth_emp:
            employee.is_authenticated = True
            employee.profile = employee
            mock_auth_emp.return_value = (employee, 'dummy_token')
            
            res = client.post(f'/api/v1/employee/complaints/{complaint_id}/verify/', {
                'verification_result': 'verified',
                'verification_remarks': 'Looks valid on site',
                'site_inspection_notes': 'Clear evidence of pothole'
            })
            print(f"Verification Status: {res.status_code}")
            if res.status_code != 200:
                print(f"Response: {res.content.decode()}")
                return
            
        print("7. Adding Progress Update via API (Employee)...")
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth_emp:
            mock_auth_emp.return_value = (employee, 'dummy_token')
            
            res = client.post(f'/api/v1/employee/complaints/{complaint_id}/progress/', {
                'progress_update': 'Started filling pothole',
                'remarks': 'Should be done soon'
            })
            print(f"Progress Status: {res.status_code}")
            if res.status_code != 200:
                print(f"Response: {res.content.decode()}")
                return

        print("8. Resolving Complaint via API (Employee)...")
        # Resolution needs an attachment proof. We can send a dummy file.
        import io
        dummy_file = io.BytesIO(b'dummy image content')
        dummy_file.name = 'proof.jpg'
        
        with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth_emp:
            mock_auth_emp.return_value = (employee, 'dummy_token')
            
            res = client.post(f'/api/v1/employee/complaints/{complaint_id}/resolve/', {
                'resolution_details': 'Pothole filled and fixed.',
                'remarks': 'All done.',
                'attachments': dummy_file
            })
            print(f"Resolution Status: {res.status_code}")
            if res.status_code != 200:
                print(f"Response: {res.content.decode()}")
                # Notice: If upload fails because Supabase storage is mocked or not working, we'll see it here!
                # Wait, I should patch upload_to_storage if it fails. Let's see if it works.

        if res.status_code == 200:
            print("9. Confirming Resolution via API (Citizen)...")
            with patch('core.authentication.supabase.SupabaseAuthentication.authenticate') as mock_auth:
                mock_auth.return_value = (citizen, 'dummy_token')
                
                res = client.post(f'/api/v1/complaints/{complaint_id}/confirm/', {
                    'confirmation_remarks': 'Thank you.'
                })
                print(f"Confirmation Status: {res.status_code}")
                if res.status_code != 200:
                    print(f"Response: {res.content.decode()}")

        print("--- END TRACE ---")

if __name__ == '__main__':
    run_e2e()
