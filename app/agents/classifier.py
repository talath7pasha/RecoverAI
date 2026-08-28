from app.models.schemas import PaymentFailureEvent, FailureCategory

class FailureClassifier:
    TRANSIENT_CODES = {
        "GATEWAY_ERROR", "NETWORK_ERROR", "BANK_SERVER_DOWN", 
        "GATEWAY_TIMEOUT", "BAD_REQUEST_ERROR"
    }
    ACTIONABLE_CODES = {
        "INSUFFICIENT_FUNDS", "PAYMENT_AUTHENTICATION_FAILED", 
        "INVALID_OTP", "INVALID_CVV", "CARD_LIMIT_EXCEEDED"
    }
    HARD_FAILURE_CODES = {
        "CARD_EXPIRED", "CARD_BLOCKED", "SUSPECTED_FRAUD", 
        "TRANSACTION_NOT_PERMITTED"
    }

    @classmethod
    def classify(cls, event: PaymentFailureEvent) -> FailureCategory:
        code = event.error_code.upper()
        if code in cls.TRANSIENT_CODES:
            return FailureCategory.TECHNICAL_TRANSIENT
        elif code in cls.ACTIONABLE_CODES:
            return FailureCategory.CUSTOMER_ACTIONABLE
        elif code in cls.HARD_FAILURE_CODES:
            return FailureCategory.HARD_FAILURE
        else:
            desc = event.error_description.lower()
            if any(k in desc for k in ["timeout", "technical", "temporary"]):
                return FailureCategory.TECHNICAL_TRANSIENT
            if any(k in desc for k in ["balance", "otp", "cvv", "limit"]):
                return FailureCategory.CUSTOMER_ACTIONABLE
            if any(k in desc for k in ["fraud", "expired", "blocked"]):
                return FailureCategory.HARD_FAILURE
            return FailureCategory.UNKNOWN