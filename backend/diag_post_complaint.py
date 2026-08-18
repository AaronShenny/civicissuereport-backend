"""
Make a real POST /api/v1/complaints/ request using a real auth token.
Usage: python diag_post_complaint.py <ACCESS_TOKEN>
Get the token from browser DevTools > Application > Local Storage > supabase session
"""
import sys
import urllib.request
import urllib.parse
import io
import uuid

if len(sys.argv) < 2:
    print("Usage: python diag_post_complaint.py <SUPABASE_ACCESS_TOKEN>")
    print("")
    print("How to get the token:")
    print("  1. Open browser DevTools (F12)")
    print("  2. Go to Application tab > Local Storage > localhost:5173")
    print("  3. Find a key starting with 'sb-' and ending with '-auth-token'")
    print("  4. Copy the 'access_token' field from its JSON value")
    sys.exit(1)

TOKEN = sys.argv[1]
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Build multipart form manually using urllib
# We'll use a simple boundary
boundary = uuid.uuid4().hex

def encode_multipart(fields, boundary):
    lines = []
    for name, value in fields.items():
        lines.append(('--' + boundary).encode())
        lines.append(('Content-Disposition: form-data; name="' + name + '"').encode())
        lines.append(b'')
        lines.append(str(value).encode('utf-8'))
    lines.append(('--' + boundary + '--').encode())
    return b'\r\n'.join(lines)

fields = {
    'category_id': '1',  # pothole
    'description': 'Test diagnostic complaint submission from diag script.',
    'state': 'Kerala',
    'district': 'Ernakulam',
    'google_maps_url': 'https://www.google.com/maps/@10.0268,76.3078,17z',
}

body = encode_multipart(fields, boundary)
content_type = 'multipart/form-data; boundary=' + boundary

print("=== POST /api/v1/complaints/ Diagnostic ===")
print("")
print("Endpoint: " + BASE_URL + "/complaints/")
print("Token: " + TOKEN[:20] + "...(truncated)")
print("Payload fields: " + str(list(fields.keys())))
print("")

req = urllib.request.Request(
    BASE_URL + "/complaints/",
    data=body,
    headers={
        'Authorization': 'Bearer ' + TOKEN,
        'Content-Type': content_type,
        'Origin': 'http://localhost:5173',
    },
    method='POST',
)

try:
    with urllib.request.urlopen(req) as resp:
        print("HTTP STATUS: " + str(resp.status))
        response_body = resp.read().decode('utf-8')
        print("RESPONSE BODY:")
        print(response_body)
        print("")
        print("[OK] Complaint submitted successfully!")
except urllib.error.HTTPError as e:
    print("HTTP STATUS: " + str(e.code))
    try:
        error_body = e.read().decode('utf-8')
        print("ERROR BODY:")
        print(error_body)
    except:
        print("Could not read error body")
except urllib.error.URLError as e:
    print("NETWORK ERROR: " + str(e.reason))
    print("Is Django running at http://127.0.0.1:8000?")
