"""
Diagnostic script for complaint submission pipeline.
Run from backend/ directory with venv activated.
"""
import os, sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

PASS = "[OK]"
FAIL = "[FAIL]"

print("=== STEP 1: Database Connection ===")
from django.db import connection
try:
    with connection.cursor() as c:
        c.execute("SELECT 1")
        c.execute("SELECT current_database()")
        db_name = c.fetchone()[0]
        c.execute("SELECT version()")
        pg_version = c.fetchone()[0][:80]
    print(PASS + " Connected to: " + db_name)
    print("    " + pg_version)
except Exception as e:
    print(FAIL + " DB connection: " + str(e))
    sys.exit(1)

print()
print("=== STEP 2: PostGIS ===")
try:
    with connection.cursor() as c:
        c.execute("SELECT PostGIS_Version()")
        pgis = c.fetchone()[0]
    print(PASS + " PostGIS version: " + pgis)
except Exception as e:
    print(FAIL + " PostGIS extension NOT available: " + str(e))
    print("    FIX: Enable PostGIS in Supabase Dashboard -> Database -> Extensions")

print()
print("=== STEP 3: ST_MakePoint (actual INSERT test) ===")
try:
    with connection.cursor() as c:
        c.execute("SELECT ST_AsText(ST_SetSRID(ST_MakePoint(76.3078, 10.0268), 4326))")
        result = c.fetchone()[0]
    print(PASS + " ST_MakePoint result: " + result)
except Exception as e:
    print(FAIL + " ST_MakePoint FAILED: " + str(e))
    print("    *** This will cause HTTP 500 on complaint submission ***")

print()
print("=== STEP 4: complaint_number_seq ===")
try:
    with connection.cursor() as c:
        c.execute("SELECT nextval('complaint_number_seq')")
        seq_val = c.fetchone()[0]
        c.execute("SELECT setval('complaint_number_seq', %s)", [seq_val - 1])
    print(PASS + " Sequence works, next val was: " + str(seq_val))
except Exception as e:
    print(FAIL + " Sequence FAILED: " + str(e))

print()
print("=== STEP 5: Location Extraction ===")
from apps.complaints.location import extract_coordinates_from_url, LocationExtractionError

tests = [
    ("Full @lat,lng URL", "https://www.google.com/maps/@10.0268,76.3078,17z"),
    ("Place URL with !3d!4d", "https://www.google.com/maps/place/Test/@9.9312,76.2673,12z/data=!4m5!3m4!1s0x0:0x0!8m2!3d9.9280!4d76.2673"),
    ("Raw coords", "10.0268,76.3078"),
]
for label, url in tests:
    try:
        lat, lng = extract_coordinates_from_url(url)
        print(PASS + " " + label + ": lat=" + str(lat) + " lng=" + str(lng))
    except LocationExtractionError as e:
        print(FAIL + " " + label + ": " + str(e))
    except Exception as e:
        print(FAIL + " " + label + " ERROR: " + type(e).__name__ + ": " + str(e))

print()
print("=== STEP 6: Active Categories ===")
from apps.complaints.models import ComplaintCategory
try:
    cats = list(ComplaintCategory.objects.filter(is_active=True).values('id', 'name'))
    print(PASS + " Active categories (" + str(len(cats)) + "):")
    for c in cats:
        print("    [" + str(c['id']) + "] " + c['name'])
except Exception as e:
    print(FAIL + " Categories: " + str(e))

print()
print("=== STEP 7: Citizen Profiles ===")
from apps.users.models import Profile, Role
try:
    citizens = list(Profile.objects.select_related('role').filter(
        role__role_name=Role.CITIZEN
    ).values('id', 'full_name')[:5])
    print(PASS + " Citizen profiles (" + str(len(citizens)) + "):")
    for p in citizens:
        print("    " + str(p['id'])[:8] + "... " + str(p['full_name']))
except Exception as e:
    print(FAIL + " Profiles: " + str(e))

print()
print("=== DONE ===")
