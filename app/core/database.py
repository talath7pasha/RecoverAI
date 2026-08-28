# app/core/database.py
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./recover_ai.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AuditLogDB(Base):
  __tablename__ = "audit_logs"

  id = Column(Integer, primary_key=True, index=True)
  event_id = Column(String, unique=True, index=True)
  payment_id = Column(String, index=True)
  customer_id = Column(String, nullable=True)
  amount = Column(Float)
  error_code = Column(String)
  failure_category = Column(String)
  action_taken = Column(String)
  recovery_probability = Column(Float)
  retry_delay_seconds = Column(Integer)
  channel = Column(String, nullable=True)
  reasoning = Column(String, nullable=True)
  status = Column(String, default="AT_RISK")  # "AT_RISK" or "RECOVERED"
  recovered_amount = Column(Float, default=0.0)
  created_at = Column(DateTime, default=datetime.utcnow)


# Alias for backward compatibility
AuditLog = AuditLogDB


def init_db():
  Base.metadata.create_all(bind=engine)


init_db()