
# app/agents/dunning_agent.py
import os
from google import genai
from app.models.schemas import PaymentFailureEvent

class DynamicDunningAgent:
    """Generates concise, context-aware dunning messages using Gemini."""

    @classmethod
    def generate_recovery_message(cls, event: PaymentFailureEvent) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Fallback template if no API key is configured
        fallback_msg = (
            f"Hi {event.customer_id}, your payment of ₹{event.amount:.2f} did not go through "
            f"due to '{event.error_description}'. Click here to complete it securely: "
            f"https://pay.rzp.io/mock/{event.payment_id}"
        )

        if not api_key:
            return fallback_msg

        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are an autonomous fintech revenue recovery agent for Razorpay.
            Generate a short, friendly, and reassuring 1-to-2 sentence message to a customer whose payment failed.
            
            Customer ID: {event.customer_id}
            Amount: INR {event.amount:.2f}
            Failure Reason: {event.error_description}
            Payment Link: https://pay.rzp.io/mock/{event.payment_id}

            Requirements:
            - Keep it under 40 words.
            - Explicitly mention the payment link.
            - Reassure the customer that their order is reserved.
            - No subject line, no placeholders.
            """

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return fallback_msg