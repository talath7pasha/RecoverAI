from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import re

app = FastAPI(title="RecoverAI Advanced Industry Engine")

events_store = []
total_at_risk = 0.0
total_recovered = 0.0

GATEWAY_HEALTH = {
    "HDFC_UPI_RAILS": {"success_rate": 42.4, "status": "DEGRADED", "latency_ms": 1240, "failover_target": "ICICI_DIRECT_SWITCH"},
    "ICICI_DIRECT_SWITCH": {"success_rate": 97.8, "status": "HEALTHY", "latency_ms": 180, "failover_target": None},
    "AXIS_AUTOPAY_SWITCH": {"success_rate": 95.1, "status": "HEALTHY", "latency_ms": 210, "failover_target": None},
    "SBI_CORE_MANDATE": {"success_rate": 58.2, "status": "CONGESTED", "latency_ms": 890, "failover_target": "AXIS_AUTOPAY_SWITCH"}
}

# Merchant SKU Margin Catalog (Real-time Unit Economics Guard)
SKU_MARGIN_CATALOG = {
    "SKU_ELECTRONICS_FLAGSHIP": {"margin_pct": 8.5, "permissible_action": "ZERO_MARGIN_PERKS_ONLY"},
    "SKU_APPAREL_LUXURY": {"margin_pct": 45.0, "permissible_action": "DYNAMIC_FLEX_INCENTIVE"},
    "SKU_SUBSCRIPTION_SaaS": {"margin_pct": 85.0, "permissible_action": "HIGH_LTV_CUSTOM_RECOVERY"}
}

class PreFailureTelemetry(BaseModel):
    session_id: str
    idle_time_seconds: float
    card_switches_count: int
    otp_hesitation: bool
    amount: float
    sku_id: Optional[str] = "SKU_ELECTRONICS_FLAGSHIP"

class SplitTenderRequest(BaseModel):
    payment_id: str
    primary_amount: float
    primary_method: str
    secondary_amount: float
    secondary_method: str

class PaymentFailureEvent(BaseModel):
    event_id: str
    payment_id: str
    customer_id: str
    customer_tier: str
    preferred_language: str
    amount: float
    error_code: str
    error_description: str
    invoice_type: Optional[str] = "D2C_CHECKOUT"
    days_overdue: Optional[int] = 0
    sku_id: Optional[str] = "SKU_ELECTRONICS_FLAGSHIP"

class SettlementRequest(BaseModel):
    payment_id: str
    amount: float
    coins_earned: int = 0

class NegotiationRequest(BaseModel):
    payment_id: str
    user_message: str
    amount: float
    customer_tier: str
    sku_id: Optional[str] = "SKU_ELECTRONICS_FLAGSHIP"

@app.get("/api/v1/telemetry/gateway-health")
def get_gateway_health():
    return GATEWAY_HEALTH

@app.post("/api/v1/telemetry/pre-failure-nudge")
def pre_failure_nudge(data: PreFailureTelemetry):
    """Intercepts dropouts before official gateway failure occurs."""
    sku_info = SKU_MARGIN_CATALOG.get(data.sku_id, {"margin_pct": 10.0, "permissible_action": "ZERO_MARGIN_PERKS_ONLY"})
    
    if data.otp_hesitation or data.idle_time_seconds >= 30:
        return {
            "intervention_triggered": True,
            "risk_type": "OTP_DROPOUT_RISK",
            "suggested_nudge": "⚡ Bank server slow? Switch to Instant 1-Tap UPI or Split into 2 installments.",
            "allowed_perks": "RecoverCoins + Express Delivery (Zero Cart Margin Loss)",
            "margin_safeguard_active": True,
            "margin_band": f"{sku_info['margin_pct']}%"
        }
    return {"intervention_triggered": False}

@app.post("/api/v1/split-tender-settle")
def split_tender_settle(req: SplitTenderRequest):
    """Aggregates balances across dual rails (e.g. UPI + Card)."""
    global total_recovered, total_at_risk
    total_val = req.primary_amount + req.secondary_amount
    total_recovered += total_val
    if total_at_risk >= total_val:
        total_at_risk -= total_val
        
    coins = int(total_val * 0.10)
    for ev in events_store:
        if ev["payment_id"] == req.payment_id:
            ev["status"] = "RECOVERED_SPLIT_TENDER"
            break
            
    return {
        "status": "SETTLED_DUAL_RAIL",
        "primary_rail": f"Charged ₹{req.primary_amount:,.2f} via {req.primary_method}",
        "secondary_rail": f"Charged ₹{req.secondary_amount:,.2f} via {req.secondary_method}",
        "coins_unlocked": coins
    }

@app.post("/api/v1/webhook/payment-failure")
def handle_failure(event: PaymentFailureEvent):
    global total_at_risk
    total_at_risk += event.amount
    
    sku_info = SKU_MARGIN_CATALOG.get(event.sku_id, {"margin_pct": 10.0, "permissible_action": "ZERO_MARGIN_PERKS_ONLY"})
    action = "EXPONENTIAL_BACKOFF_RETRY"
    failure_cat = "TECHNICAL_GATEWAY_ERROR"
    reasoning = "Switch timeout detected; scheduling retries."
    prob = 0.85
    channel = "WhatsApp"
    active_switch = "HDFC_UPI_RAILS"
    rerouted_switch = None

    if "TECHNICAL" in event.error_code or "SWITCH" in event.error_code or "TIMEOUT" in event.error_code:
        rerouted_switch = GATEWAY_HEALTH["HDFC_UPI_RAILS"]["failover_target"]
        action = "AUTONOMOUS_PSP_FAILOVER_REROUTE"
        reasoning = f"HDFC UPI Rails degraded (42.4%). Auto-cascaded to {rerouted_switch} (97.8% health)."
        prob = 0.94
        channel = "WhatsApp"

    elif event.invoice_type == "B2B_INVOICE" or event.days_overdue > 0:
        failure_cat = "B2B_RECEIVABLES_OVERDUE"
        if event.days_overdue <= 3:
            action = "B2B_GENTLE_RECOVERY_NUDGE"
            reasoning = f"Net-30 Invoice {event.days_overdue} days overdue. Dispatched statement."
            prob = 0.91
            channel = "Email"
        elif event.days_overdue <= 10:
            action = "B2B_EARLY_SETTLEMENT_INCENTIVE"
            reasoning = f"Invoice {event.days_overdue} days overdue. Offering early clearance platform credits."
            prob = 0.78
            channel = "WhatsApp"
        else:
            action = "B2B_EXECUTIVE_ESCALATION"
            reasoning = f"Invoice aging critical ({event.days_overdue} days). Auto-escalated to Key Account Manager."
            prob = 0.45
            channel = "Executive Desk"

    elif event.invoice_type == "SUBSCRIPTION_MANDATE" or "MANDATE" in event.error_code:
        failure_cat = "SUBSCRIPTION_MANDATE_FAILURE"
        action = "SMART_SALARY_CYCLE_RETRY"
        reasoning = "AutoPay recurring debit failed. Sequenced next retry at optimal salary window (07:00 AM)."
        prob = 0.88
        channel = "In-App Push"

    elif "INSUFFICIENT" in event.error_code:
        failure_cat = "INSUFFICIENT_FUNDS"
        action = "SPLIT_PAYMENT_RECOVERY"
        reasoning = "Insufficient funds detected; offering multi-account split tender recovery."
        prob = 0.92
    elif "FRAUD" in event.error_code:
        failure_cat = "SUSPECTED_FRAUD"
        action = "HALT_FRAUD_PREVENTION"
        reasoning = "High-risk velocity flag; halting automated retry."
        prob = 0.05
        channel = "Email"
    elif "AUTH" in event.error_code:
        failure_cat = "AUTHENTICATION_FAILURE"
        action = "ONE_TAP_UPI_LINK"
        reasoning = "OTP timeout; rerouting to 1-Tap UPI flow."
        prob = 0.89

    entry = {
        "event_id": event.event_id,
        "payment_id": event.payment_id,
        "amount": event.amount,
        "failure_category": failure_cat,
        "action_taken": action,
        "recovery_probability": prob,
        "channel": channel,
        "status": "AT_RISK",
        "reasoning": reasoning,
        "coins_credited": int(event.amount * 0.10),
        "invoice_type": event.invoice_type,
        "days_overdue": event.days_overdue,
        "active_gateway_switch": rerouted_switch or active_switch,
        "sku_margin_pct": sku_info["margin_pct"]
    }
    events_store.insert(0, entry)
    return {"status": "ACK", "processed_action": action}

@app.post("/api/v1/settle-recovery")
def settle_recovery(req: SettlementRequest):
    global total_recovered, total_at_risk
    for ev in events_store:
        if ev["payment_id"] == req.payment_id:
            ev["status"] = "RECOVERED"
            total_recovered += req.amount
            if total_at_risk >= req.amount:
                total_at_risk -= req.amount
            break
    return {"status": "SETTLED", "payment_id": req.payment_id, "coins_unlocked": req.coins_earned}

@app.post("/api/v1/conversational-negotiate")
def negotiate(req: NegotiationRequest):
    txt = req.user_message.lower().strip()
    adjusted = req.amount
    coins = int(req.amount * 0.10)
    action = "FALLBACK"
    
    sku_info = SKU_MARGIN_CATALOG.get(req.sku_id, {"margin_pct": 8.5, "permissible_action": "ZERO_MARGIN_PERKS_ONLY"})
    hinglish_words = ["bhai", "hai", "nahi", "kardo", "karo", "karna", "paise", "kuch", "milega", "bhejo", "kab", "dena", "parso", "kya", "aadha", "aayegi", "mat", "bhejna", "chahiye"]
    is_hinglish = any(re.search(rf"\b{w}\b", txt) for w in hinglish_words)

    # 1. Promise-to-Pay (PTP)
    if any(k in txt for k in ["tomorrow", "friday", "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday", "next week", "later", "pay on", "salary", "kal", "parso", "baad me"]):
        action = "PROMISE_TO_PAY_LOGGED"
        if is_hinglish:
            reply = f"📅 **Promise-to-Pay Confirm ho gaya!** Humne aapka order hold pe rakh diya hai aur alerts pause kar diye hain. Scheduled date pe 1-Tap link mil jayegi. Saath me **{coins} RecoverCoins** bhi milenge!"
        else:
            reply = f"📅 **Promise-to-Pay Confirmed!** We have locked your order and paused all recovery alerts. We will send a 1-Tap link on your scheduled date. You will still earn {coins} RecoverCoins!"

    # 2. Compliance Opt-Out
    elif any(k in txt for k in ["stop", "don't message", "cancel", "opt out", "unsubscribe", "mat bhejo", "spam", "band karo", "mat bhej"]):
        action = "COMPLIANCE_OPTOUT_SUPPRESSED"
        if is_hinglish:
            reply = "🛑 **Outreach Suppress kar diya gaya:** Humne aapki request note kar li hai. Anti-Harassment policy ke tehat saare automatic alerts turant band kar diye gaye hain."
        else:
            reply = "🛑 **Outreach Suppressed:** All automated outreach has been immediately stopped in compliance with our Anti-Harassment policy."

    # 3. Split-Payment / Split-Tender
    elif any(k in txt for k in ["split", "part", "half", "two", "install", "installment", "aadha", "tukde", "balance"]):
        action = "SPLIT_PAY_APPROVED"
        adjusted = req.amount / 2
        if is_hinglish:
            reply = f"✅ **Split-Pay / Dual-Tender Activate ho gaya!** Abhi sirf ₹{adjusted:,.2f} (Part 1) pay karein, baaki amount 14 din baad. Saath me **{coins} RecoverCoins** bhi confirmed!"
        else:
            reply = f"✅ **Split-Tender Activated!** Pay ₹{adjusted:,.2f} now (Part 1) and the rest in 14 days or across dual payment methods. You still earn {coins} RecoverCoins!"

    # 4. RecoverCoins / Perks (Bounded by SKU Margin Guard)
    elif any(k in txt for k in ["coin", "point", "reward", "offer", "discount", "perk", "deal", "cashback", "kuch kam", "kam karo"]):
        action = "RECOVER_COINS_UNLOCKED"
        margin_guard_note = f"[🛡️ SKU Margin Guard: {sku_info['margin_pct']}% Margin Protected — Zero Cart Discount]"
        if is_hinglish:
            reply = f"🪙 **Reward Multiplier Active!** {margin_guard_note}\n\nAbhi order complete karne par aapko milenge **{coins} RecoverCoins** (Value: ₹{coins/10:,.2f} cash agle order ke liye) + Free Express Delivery!"
        else:
            reply = f"🪙 **Instant Reward Multiplier Active!** {margin_guard_note}\n\nComplete payment now to earn **{coins} RecoverCoins** (Value: ₹{coins/10:,.2f} cash credit for next order) + Free Express Priority Delivery!"

    # 5. Direct UPI Link
    elif any(k in txt for k in ["upi", "link", "pay", "gpay", "phonepe", "qr", "bhejo"]):
        action = "UPI_ONE_TAP_APPROVED"
        if is_hinglish:
            reply = f"⚡ **Direct 1-Tap UPI Link ready hai.** Turant checkout karein aur apne **{coins} RecoverCoins** secure karein."
        else:
            reply = f"⚡ Direct 1-Tap UPI link configured. Complete now to secure your {coins} bonus coins."

    else:
        if is_hinglish:
            reply = f"Hum aapki ₹{req.amount:,.2f} payment resolve karne me madad kar sakte hain. Aap 'Split', 'Coins offer', ya 'UPI link' likhkar reply kar sakte hain."
        else:
            reply = "I can assist you with completing this recovery payment. Reply with 'Split', 'Coins offer', or 'UPI link'."

    checkout = f"http://localhost:8501/?checkout_id={req.payment_id}&amt={adjusted}&coins={coins}&sku_margin={sku_info['margin_pct']}"
    return {"reply": reply, "action": action, "adjusted_amount": adjusted, "coins": coins, "checkout_url": checkout, "sku_margin": sku_info["margin_pct"]}

@app.get("/api/v1/metrics")
def get_metrics():
    total_ev = len(events_store)
    yield_rate = round((total_recovered / (total_at_risk + total_recovered) * 100), 2) if (total_at_risk + total_recovered) > 0 else 0.0
    return {
        "total_revenue_at_risk_inr": total_at_risk,
        "total_revenue_recovered_inr": total_recovered,
        "recovery_rate_percentage": yield_rate,
        "total_events_processed": total_ev,
        "recent_logs": events_store[:15]
    }

@app.post("/api/v1/reset-ledger")
def reset():
    global total_at_risk, total_recovered
    events_store.clear()
    total_at_risk = 0.0
    total_recovered = 0.0
    return {"status": "CLEARED"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)