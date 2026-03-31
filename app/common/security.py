import hmac
import hashlib
from fastapi import Request, HTTPException

def compute_hmac_signature(raw_body: bytes, secret: str, ts: str) -> str:
    message = f"{ts}.{raw_body.decode('utf-8')}".encode()
    sig = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"

async def verify_hmac_signature(request: Request, secret: str):
    body = await request.body()
    sig_header = request.headers.get("X-Webhook-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing X-Webhook-Signature header")
    
    try:
        parts = {p.split("=")[0]: p.split("=")[1] for p in sig_header.split(",")}
        ts = parts.get("t")
        received_sig = parts.get("v1")
    except (IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid X-Webhook-Signature format")

    if not ts or not received_sig:
        raise HTTPException(status_code=400, detail="Invalid X-Webhook-Signature format")

    expected_sig_full = compute_hmac_signature(body, secret, ts)
    expected_sig = expected_sig_full.split("v1=")[1]

    if not hmac.compare_digest(expected_sig, received_sig):
        raise HTTPException(status_code=403, detail="Invalid HMAC signature")
    
    return True
