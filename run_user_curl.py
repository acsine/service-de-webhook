import requests
import json

url = 'http://localhost:8001/api/v1/events'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbGllbnQtODZkNmFmIiwidGVuYW50X2lkIjoiNmNkZGZmZmItM2Y2MC00ZWZkLTgwZTUtZWYxYzk5YzRhOTc3Iiwic2NvcGUiOiJ3ZWJob29rczpwdWJsaXNoIiwiaWF0IjoxNzc0ODkwMzUyLCJleHAiOjE3NzQ4OTM5NTIsIm0ybSI6dHJ1ZX0.qYhV9U5QWQhFPmBwHABgy6I3vtnjwU'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
data = {
    'event_type': 'user.created',
    'tenant_id': '6cddfffb-3f60-4efd-80e5-ef1c99c4a977',
    'payload': {'additionalProp1': {}},
    'target_app_id': 'app_18967e96',
    'idempotency_key': 'test_unique_final_logged_102'
}

resp = requests.post(url, headers=headers, json=data)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.text}')
