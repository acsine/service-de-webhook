import requests
import json

url = 'http://localhost:8001/api/v1/events'
# Read token from full_token.txt
with open('full_token.txt', 'r', encoding='utf-16') as f:
    token = f.read().strip()

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
data = {
    'event_type': 'app.push', # Added the dot
    'tenant_id': '6cddfffb-3f60-4efd-80e5-ef1c99c4a977',
    'payload': {'test': 'callback_url_logging_v2'},
    'idempotency_key': 'test_url_logging_v1_500'
}

resp = requests.post(url, headers=headers, json=data)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.text}')
