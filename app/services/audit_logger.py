# app/services/audit_logger.py
from typing import Any, Dict
from app.core.database import AuditLogDB, SessionLocal
from app.models.schemas import PaymentFailureEvent, RecoveryDecision


class AuditLedgerService:

  @classmethod
  def record_decision(
      cls, event: PaymentFailureEvent, decision: RecoveryDecision
  ):
    db = SessionLocal()
    try:
      record = AuditLogDB(
          event_id=event.event_id,
          payment_id=event.payment_id,
          customer_id=event.customer_id,
          amount=event.amount,
          error_code=event.error_code,
          failure_category=decision.failure_category.value,
          action_taken=decision.recommended_action.value,
          recovery_probability=decision.recovery_probability,
          retry_delay_seconds=decision.retry_delay_seconds,
          channel=decision.channel,
          reasoning=decision.reasoning,
          status="AT_RISK",
          recovered_amount=0.0,
      )
      db.add(record)
      db.commit()
    finally:
      db.close()

  @classmethod
  def mark_recovered(cls, payment_id: str, amount: float):
    db = SessionLocal()
    try:
      record = (
          db.query(AuditLogDB)
          .filter(AuditLogDB.payment_id == payment_id)
          .first()
      )
      if record:
        record.status = "RECOVERED"
        record.recovered_amount = amount
        db.commit()
    finally:
      db.close()

  @classmethod
  def get_metrics(cls) -> Dict[str, Any]:
    db = SessionLocal()
    try:
      logs = db.query(AuditLogDB).order_by(AuditLogDB.id.desc()).all()
      total_risk = sum(log.amount for log in logs)
      total_recovered = sum(
          log.recovered_amount for log in logs if log.status == "RECOVERED"
      )
      rate = (total_recovered / total_risk * 100) if total_risk > 0 else 0.0

      return {
          "total_revenue_at_risk_inr": round(total_risk, 2),
          "total_revenue_recovered_inr": round(total_recovered, 2),
          "recovery_rate_percentage": round(rate, 2),
          "total_events_processed": len(logs),
          "recent_logs": [
              {
                  "payment_id": log.payment_id,
                  "amount": log.amount,
                  "failure_category": log.failure_category,
                  "action_taken": log.action_taken,
                  "recovery_probability": log.recovery_probability,
                  "channel": log.channel,
                  "status": log.status,
                  "reasoning": log.reasoning,
              }
              for log in logs[:15]
          ],
      }
    finally:
      db.close()