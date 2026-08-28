# tests/simulate_events.py
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

MOCK_FAILURES = [
    {
        "event_id": "evt_101",
        "payment_id": "pay_timeout_001",
        "customer_id": "cust_rahul",
        "customer_email": "rahul@example.com",
        "customer_phone": "+919876543210",
        "amount": 1499.00,
        "currency": "INR",
        "error_code": "GATEWAY_TIMEOUT",
        "error_description": "Bank gateway timed out during processing",
        "retry_count": 0
    },
    {
        "event_id": "evt_102",
        "payment_id": "pay_insufficient_002",
        "customer_id": "cust_sneha",
        "customer_email": "sneha@example.com",
        "customer_phone": "+919812345678",
        "amount": 4200.00,
        "currency": "INR",
        "error_code": "INSUFFICIENT_FUNDS",
        "error_description": "Account balance insufficient for debit",
        "retry_count": 0
    },
    {
        "event_id": "evt_103",
        "payment_id": "pay_fraud_003",
        "customer_id": "cust_badactor",
        "customer_email": "suspicious@domain.com",
        "customer_phone": None,
        "amount": 89000.00,
        "currency": "INR",
        "error_code": "SUSPECTED_FRAUD",
        "error_description": "High risk velocity flag triggered",
        "retry_count": 0
    },
    {
        "event_id": "evt_104",
        "payment_id": "pay_max_retries_004",
        "customer_id": "cust_amit",
        "customer_email": "amit@example.com",
        "customer_phone": "+919765432109",
        "amount": 2999.00,
        "currency": "INR",
        "error_code": "GATEWAY_ERROR",
        "error_description": "Repeated network error",
        "retry_count": 3
    }
]

def run_simulation():
    print("🚀 1. Simulating Razorpay Failed Payment Webhooks...")
    for event in MOCK_FAILURES:
        res = requests.post(f"{BASE_URL}/webhook/razorpay/payment-failed", json=event)
        print(f"   [INBOUND FAILURE] {event['payment_id']} ({event['error_code']}) -> Status: {res.status_code}")
        time.sleep(0.3)

    print("\n⚡ 2. Simulating Customer Converting via RecoverAI Dunning Link...")
    # Customer Sneha pays via the WhatsApp link
    success_payload = {
        "payment_id": "pay_insufficient_002",
        "amount": 4200.00,
        "recovery_channel": "WHATSAPP_SMART_DUNNING"
    }
    res_succ = requests.post(f"{BASE_URL}/webhook/razorpay/payment-success", json=success_payload)
    print(f"   [REVENUE RECOVERED] {success_payload['payment_id']} -> Recovered ₹{success_payload['amount']}")

    print("\n📊 3. Fetching Aggregated Ledger Metrics...")
    time.sleep(0.5)
    metrics = requests.get(f"{BASE_URL}/metrics").json()
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    run_simulation()