# main.py
import os
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.models.schemas import PaymentFailureEvent, RecoveryDecision, FailureCategory, RecoveryActionType
from app.agents.graph_engine import recovery_agent_graph
from app.services.audit_logger import AuditLedgerService
from app.core.security import verify_razorpay_signature
from app.core.database import SessionLocal, AuditLog

app = FastAPI(
    title="RecoverAI: Intelligent Revenue Recovery Agent",
    description="Multi-Agent payment recovery engine built with LangGraph for Razorpay Track 3",
    version="2.2.0"
)

class PaymentSuccessEvent(BaseModel):
    payment_id: str
    amount: float
    recovery_channel: Optional[str] = "RECOVER_AI_LINK"

def execute_recovery_pipeline(event: PaymentFailureEvent):
    initial_state = {
        "event": event.dict(),
        "failure_category": None,
        "root_cause_analysis": None,
        "is_halted": False,
        "halt_reason": None,
        "recovery_action": None,
        "recovery_probability": 0.0,
        "retry_delay_seconds": 0,
        "channel": None,
        "upi_intent_uri": None,
        "incentive_data": None,
        "dunning_message": None,
        "logs": []
    }

    final_state = recovery_agent_graph.invoke(initial_state)

    decision = RecoveryDecision(
        payment_id=event.payment_id,
        failure_category=FailureCategory(final_state["failure_category"]),
        recommended_action=RecoveryActionType(final_state["recovery_action"]),
        recovery_probability=final_state["recovery_probability"],
        retry_delay_seconds=final_state["retry_delay_seconds"],
        channel=final_state.get("channel"),
        reasoning=final_state["root_cause_analysis"] if not final_state["is_halted"] else final_state["halt_reason"],
        dunning_message=final_state.get("dunning_message")
    )

    AuditLedgerService.record_decision(event, decision)

    print("\n" + "="*60)
    print(f"🤖 [LangGraph Multi-Agent Telemetry] Payment: {event.payment_id}")
    for log in final_state["logs"]:
        print(f"  {log}")
    print("="*60)

# --- Interactive 1-Click Recovery Payment Screen ---
@app.get("/pay/{payment_id}", response_class=HTMLResponse)
async def serve_recovery_checkout(payment_id: str, amt: float = 1499.00):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RecoverAI Smart Checkout</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px; width: 100%; max-width: 420px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
            .brand {{ color: #38bdf8; font-weight: 700; font-size: 1.25rem; display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }}
            .amount-box {{ background: #0f172a; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; border: 1px solid #1e293b; }}
            .amount {{ font-size: 2.2rem; font-weight: 700; color: #10b981; margin: 4px 0; }}
            .btn {{ background: linear-gradient(135deg, #0284c7, #2563eb); color: white; border: none; padding: 14px 20px; border-radius: 10px; width: 100%; font-size: 1rem; font-weight: 600; cursor: pointer; transition: 0.2s; }}
            .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
            .secure {{ text-align: center; font-size: 0.75rem; color: #94a3b8; margin-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="brand">💳 RecoverAI Smart Checkout</div>
            <p style="color: #94a3b8; font-size: 0.9rem;">Your previous attempt failed. Complete your order instantly via our intelligent rescue link.</p>
            <div class="amount-box">
                <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Amount Payable</div>
                <div class="amount">₹{amt:,.2f}</div>
                <div style="font-size: 0.8rem; color: #64748b;">Reference: {payment_id}</div>
            </div>
            <button class="btn" onclick="completePayment()">⚡ Complete 1-Tap Recovery</button>
            <div class="secure">🔒 Encrypted via Razorpay Autonomous Recovery Agent</div>
        </div>
        <script>
            async function completePayment() {{
                const btn = document.querySelector('.btn');
                btn.innerText = "Processing...";
                btn.disabled = true;
                try {{
                    const res = await fetch('/webhook/razorpay/payment-success', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ payment_id: '{payment_id}', amount: {amt} }})
                    }});
                    if (res.ok) {{
                        document.querySelector('.card').innerHTML = `
                            <div style="text-align:center; padding: 20px 0;">
                                <div style="font-size: 3rem;">✅</div>
                                <h2 style="color: #10b981; margin: 12px 0;">Payment Recovered!</h2>
                                <p style="color: #94a3b8; font-size: 0.9rem;">₹{amt:,.2f} has been recovered and updated live on the Streamlit dashboard.</p>
                                <button class="btn" style="margin-top: 16px;" onclick="window.close()">Close Window</button>
                            </div>
                        `;
                    }}
                }} catch(e) {{
                    alert("Error settling mock recovery");
                    btn.disabled = false;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/webhook/razorpay/payment-failed")
async def handle_payment_failure(
    event: PaymentFailureEvent, 
    background_tasks: BackgroundTasks,
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):
    if x_razorpay_signature:
        raw_body = await request.body()
        if not verify_razorpay_signature(raw_body, x_razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid Razorpay Webhook Signature")

    background_tasks.add_task(execute_recovery_pipeline, event)
    return {"status": "ORCHESTRATED_BY_LANGGRAPH", "payment_id": event.payment_id}

@app.post("/webhook/razorpay/payment-success")
async def handle_payment_success(event: PaymentSuccessEvent):
    AuditLedgerService.mark_recovered(event.payment_id, event.amount)
    return {"status": "RECORDED_RECOVERED_REVENUE", "payment_id": event.payment_id, "amount": event.amount}

@app.post("/reset-ledger")
async def reset_database():
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.commit()
        return {"status": "SUCCESS", "message": "Audit ledger cleared"}
    finally:
        db.close()

@app.get("/metrics")
async def get_dashboard_metrics():
    return AuditLedgerService.get_metrics()

@app.get("/")
def health_check():
    return {"status": "online", "engine": "LangGraph Multi-Agent State Machine"}