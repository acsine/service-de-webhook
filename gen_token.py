import time
from jose import jwt
import os

# From .env
SECRET_KEY = os.getenv("SECRET_KEY", "yoursecretkey")
ALGORITHM = "HS256"

def generate_token():
    payload = {
        "sub": "client-86d6af",
        "tenant_id": "6cddfffb-3f60-4efd-80e5-ef1c99c4a977",
        "scope": "webhooks:publish",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600, # 1 hour
        "m2m": True
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

if __name__ == "__main__":
    token = generate_token()
    print(token)
