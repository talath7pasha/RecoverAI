# app/agents/advanced_engines.py
import urllib.parse
import random
from typing import Dict, Any, Optional

class UPIIntentEngine:
    """
    Generates standardized NPCI/Razorpay UPI Deep-Link Intent URIs
    for 1-tap mobile app-switch recovery (GPay, PhonePe, Paytm, CRED).
    """
    MERCHANT_VPA = "recoverai.merchant@razorpay"
    MERCHANT_NAME = "RecoverAI Store"

    @classmethod
    def generate_upi_uri(cls, payment_id: str, amount: float, note: str = "Order Recovery") -> str:
        params = {
            "pa": cls.MERCHANT_VPA,
            "pn": cls.MERCHANT_NAME,
            "tr": payment_id,
            "am": f"{amount:.2f}",
            "cu": "INR",
            "tn": note
        }
        return f"upi://pay?{urllib.parse.urlencode(params)}"


class ContextualBanditOptimizer:
    """
    Reinforcement Learning (Epsilon-Greedy Multi-Armed Bandit)
    Adaptively selects the optimal recovery channel based on amount tiers and historical reward conversions.
    """
    # Channel conversion rewards history
    ARM_REWARDS = {
        "WHATSAPP_UPI_INTENT": {"trials": 42, "successes": 31}, # ~73% yield
        "EMAIL_SMART_LINK": {"trials": 35, "successes": 14},    # ~40% yield
        "SMS_DIRECT_RETRY": {"trials": 20, "successes": 8},      # ~40% yield
        "SILENT_GATEWAY_RETRY": {"trials": 50, "successes": 41}  # ~82% for transient
    }
    EPSILON = 0.15  # 15% exploration, 85% exploitation

    @classmethod
    def select_optimal_channel(cls, category: str, amount: float, has_phone: bool) -> str:
        if category == "technical_transient":
            return "SILENT_GATEWAY_RETRY"

        if not has_phone:
            return "EMAIL_SMART_LINK"

        # Exploration vs Exploitation
        if random.random() < cls.EPSILON:
            # Explore random available channel
            return random.choice(["WHATSAPP_UPI_INTENT", "SMS_DIRECT_RETRY", "EMAIL_SMART_LINK"])

        # Exploit: pick highest estimated empirical conversion rate
        best_channel = "WHATSAPP_UPI_INTENT"
        best_rate = -1.0
        candidate_arms = ["WHATSAPP_UPI_INTENT", "SMS_DIRECT_RETRY", "EMAIL_SMART_LINK"]

        for arm in candidate_arms:
            data = cls.ARM_REWARDS[arm]
            rate = data["successes"] / data["trials"] if data["trials"] > 0 else 0.5
            if rate > best_rate:
                best_rate = rate
                best_channel = arm

        return best_channel

    @classmethod
    def record_feedback(cls, channel: str, converted: bool):
        if channel in cls.ARM_REWARDS:
            cls.ARM_REWARDS[channel]["trials"] += 1
            if converted:
                cls.ARM_REWARDS[channel]["successes"] += 1


class DynamicIncentiveNegotiator:
    """
    Autonomous cart-saving negotiation sub-agent.
    If high value (> ₹3,000) and friction detected (INSUFFICIENT_FUNDS),
    synthesizes bounded 5% emergency discount or EMI split-pay nudge.
    """
    HIGH_VALUE_THRESHOLD = 3000.0
    MAX_DISCOUNT_PERCENT = 5.0

    @classmethod
    def evaluate_incentive(cls, error_code: str, amount: float) -> Optional[Dict[str, Any]]:
        if amount >= cls.HIGH_VALUE_THRESHOLD and error_code in ["INSUFFICIENT_FUNDS", "PAYMENT_AUTHENTICATION_FAILED"]:
            discount_val = round((amount * cls.MAX_DISCOUNT_PERCENT) / 100, 2)
            adjusted_amt = amount - discount_val
            return {
                "incentive_applied": True,
                "strategy": "AUTONOMOUS_FRICTION_DISCOUNT",
                "discount_percent": cls.MAX_DISCOUNT_PERCENT,
                "discount_amount": discount_val,
                "adjusted_amount": adjusted_amt,
                "reasoning": f"High friction detected on cart ₹{amount:,.2f}. Authorized emergency {cls.MAX_DISCOUNT_PERCENT}% liquidity relief."
            }
        return None