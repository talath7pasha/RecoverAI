from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FailureCategory(str, Enum):
    TECHNICAL_TRANSIENT = "technical_transient"
    CUSTOMER_ACTIONABLE = "customer_actionable"
    HARD_FAILURE = "hard_failure"
    UNKNOWN = "unknown"

class RecoveryActionType(str, Enum):
    AUTO_RETRY = "auto_retry"
    SMART_DUNNING = "smart_dunning"
    ALTERNATIVE_PAYMENT = "alternative_payment"
    ESCALATE_MANUAL = "escalate_manual"
    TERMINATE = "terminate"

class PaymentFailureEvent(BaseModel):
    event_id: str
    payment_id: str
    order_id: Optional[str] = None
    customer_id: str
    customer_email: str
    customer_phone: Optional[str] = None
    amount: float
    currency: str = "INR"
    error_code: str
    error_description: str
    retry_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class RecoveryDecision(BaseModel):
    payment_id: str
    failure_category: FailureCategory
    recommended_action: RecoveryActionType
    recovery_probability: float
    retry_delay_seconds: int = 0
    channel: Optional[str] = None
    reasoning: str
    dunning_message: Optional[str] = None
    audit_timestamp: datetime = Field(default_factory=datetime.utcnow)