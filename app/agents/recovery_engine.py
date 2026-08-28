# app/agents/recovery_engine.py
from app.models.schemas import (
    PaymentFailureEvent, 
    RecoveryDecision, 
    FailureCategory, 
    RecoveryActionType
)
from app.agents.classifier import FailureClassifier
from app.agents.dunning_agent import DynamicDunningAgent

class RecoveryDecisionEngine:
    MAX_RETRIES = 3

    @classmethod
    def evaluate(cls, event: PaymentFailureEvent) -> RecoveryDecision:
        if event.retry_count >= cls.MAX_RETRIES:
            return RecoveryDecision(
                payment_id=event.payment_id,
                failure_category=FailureCategory.UNKNOWN,
                recommended_action=RecoveryActionType.TERMINATE,
                recovery_probability=0.0,
                retry_delay_seconds=0,
                reasoning=f"Stopping rule triggered: Max retries ({cls.MAX_RETRIES}) reached."
            )

        category = FailureClassifier.classify(event)

        if category == FailureCategory.TECHNICAL_TRANSIENT:
            delays = [30, 120, 300]
            delay = delays[min(event.retry_count, len(delays) - 1)]
            return RecoveryDecision(
                payment_id=event.payment_id,
                failure_category=category,
                recommended_action=RecoveryActionType.AUTO_RETRY,
                recovery_probability=0.85,
                retry_delay_seconds=delay,
                channel="DIRECT_API",
                reasoning=f"Transient technical error. Scheduled silent retry in {delay}s."
            )

        elif category == FailureCategory.CUSTOMER_ACTIONABLE:
            # Generate tailored message via GenAI agent
            msg = DynamicDunningAgent.generate_recovery_message(event)
            return RecoveryDecision(
                payment_id=event.payment_id,
                failure_category=category,
                recommended_action=RecoveryActionType.SMART_DUNNING,
                recovery_probability=0.65,
                retry_delay_seconds=0,
                channel="WHATSAPP" if event.customer_phone else "EMAIL",
                dunning_message=msg,
                reasoning="Customer actionable error. Dynamic payment link generated via GenAI."
            )

        elif category == FailureCategory.HARD_FAILURE:
            return RecoveryDecision(
                payment_id=event.payment_id,
                failure_category=category,
                recommended_action=RecoveryActionType.ALTERNATIVE_PAYMENT,
                recovery_probability=0.35,
                retry_delay_seconds=0,
                channel="EMAIL",
                dunning_message=f"Your card could not be charged ({event.error_description}). Please update your billing method.",
                reasoning="Hard failure. Immediate retries suppressed to prevent fees."
            )

        else:
            return RecoveryDecision(
                payment_id=event.payment_id,
                failure_category=FailureCategory.UNKNOWN,
                recommended_action=RecoveryActionType.ESCALATE_MANUAL,
                recovery_probability=0.20,
                retry_delay_seconds=0,
                reasoning="Unrecognized error pattern. Escalated to manual queue."
            )