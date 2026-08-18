import os
import requests

SUPABASE_URL = "https://eucpbycjwfbaxzutwpoe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y3BieWNqd2ZiYXh6dXR3cG9lIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4Njk4NTc2NSwiZXhwIjoyMTAyNTYxNzY1fQ.iTvYI4qCjmKNDBQmlPWYdZlKm7HzmUtafeA_aMqMi58"

def create_user(email, password):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Create user in Auth
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"Successfully created user: {email}")
        user_id = response.json().get('id')
        print(f"User ID: {user_id}")
    else:
        print(f"Failed to create user: {response.text}")

if __name__ == "__main__":
    create_user("testcitizen@example.com", "TestPassword123!")
