# app/core/security.py
import hmac
import hashlib
import os

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "mock_secret_key_recover_ai_2026")

def verify_razorpay_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Validates Razorpay's HMAC-SHA256 signature against the raw payload bytes.
    """
    if not signature_header:
        return False
        
    expected_signature = hmac.new(
        key=RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)