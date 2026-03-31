import requests
import json

url = "http://localhost:8001/api/v1/events"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbGllbnQtODZkNmFmIiwidGVuYW50X2lkIjoiNmNkZGZmZmItM2Y2MC00ZWZkLTgwZTUtZWYxYzk5YzRhOTc3Iiwic2NvcGUiOiJ3ZWJob29rczpwdWJsaXNoIiwiaWF0IjoxNzc0ODg5Mjg4LCJleHAiOjE3NzQ4OTI4ODgsIm0ybSI6dHJ1ZX0.kTt_u07UzyvAk4HMtRvnHRwfHAZtOu8_ay1GiVnWYgE",
    "Content-Type": "application/json"
}
data = {
    "event_type": "app.test",  # Namespace format required by regex
    "tenant_id": "6cddfffb-3f60-4efd-80e5-ef1c99c4a977",
    "payload": {"test": "stabilization_confirmed"},
    "idempotency_key": "verified_success_v2_100"
}

response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
