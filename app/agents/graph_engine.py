# app/agents/graph_engine.py
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from app.models.schemas import FailureCategory, RecoveryActionType
from app.agents.advanced_engines import UPIIntentEngine, ContextualBanditOptimizer, DynamicIncentiveNegotiator

# Shared Multi-Agent State
class AgentState(TypedDict):
    event: Dict[str, Any]
    failure_category: Optional[str]
    root_cause_analysis: Optional[str]
    is_halted: bool
    halt_reason: Optional[str]
    recovery_action: Optional[str]
    recovery_probability: float
    retry_delay_seconds: int
    channel: Optional[str]
    upi_intent_uri: Optional[str]
    incentive_data: Optional[Dict[str, Any]]
    dunning_message: Optional[str]
    logs: List[str]


# --- 1. Diagnostic Agent ---
def diagnostic_agent(state: AgentState) -> AgentState:
    event = state["event"]
    code = event.get("error_code", "").upper()
    logs = state.get("logs", [])
    
    logs.append(f"🔍 [Diagnostic Agent] Telemetry Code: {code}")

    if code in ["GATEWAY_ERROR", "NETWORK_ERROR", "BANK_SERVER_DOWN", "GATEWAY_TIMEOUT"]:
        category = FailureCategory.TECHNICAL_TRANSIENT.value
        analysis = f"Transient gateway timeout ({code}). Issuer or network dropped connection."
    elif code in ["INSUFFICIENT_FUNDS", "PAYMENT_AUTHENTICATION_FAILED", "INVALID_OTP", "INVALID_CVV"]:
        category = FailureCategory.CUSTOMER_ACTIONABLE.value
        analysis = f"Customer actionable friction ({code}). Liquidity or OTP dropped."
    elif code in ["CARD_EXPIRED", "CARD_BLOCKED", "SUSPECTED_FRAUD"]:
        category = FailureCategory.HARD_FAILURE.value
        analysis = f"Terminal hard error ({code}). Card velocity or authorization failed."
    else:
        category = FailureCategory.UNKNOWN.value
        analysis = f"Unmapped error signature ({code})."

    logs.append(f"✅ [Diagnostic Agent] Diagnosis: {category.upper()} -> {analysis}")
    return {**state, "failure_category": category, "root_cause_analysis": analysis, "logs": logs}


# --- 2. Policy & RL Bandit Optimization Agent ---
def policy_guardrail_agent(state: AgentState) -> AgentState:
    event = state["event"]
    category = state["failure_category"]
    retry_count = event.get("retry_count", 0)
    amount = float(event.get("amount", 0.0))
    has_phone = bool(event.get("customer_phone"))
    logs = state.get("logs", [])

    # Stopping Guardrails
    if retry_count >= 3:
        logs.append("⛔ [Policy Agent] Stopping Rule: Exceeded 3 max retries. Halting.")
        return {
            **state,
            "is_halted": True,
            "halt_reason": "Max retries (3) reached. Suppressing attempts to save merchant fees.",
            "recovery_action": RecoveryActionType.TERMINATE.value,
            "recovery_probability": 0.0,
            "retry_delay_seconds": 0,
            "channel": None,
            "logs": logs
        }

    # Contextual Multi-Armed Bandit Channel Optimization
    selected_channel = ContextualBanditOptimizer.select_optimal_channel(category, amount, has_phone)
    logs.append(f"🧠 [Bandit RL Optimizer] Exploiting best historical channel: [{selected_channel}]")

    if category == FailureCategory.TECHNICAL_TRANSIENT.value:
        delays = [30, 120, 300]
        delay = delays[min(retry_count, len(delays) - 1)]
        return {
            **state,
            "is_halted": False,
            "recovery_action": RecoveryActionType.AUTO_RETRY.value,
            "recovery_probability": 0.88,
            "retry_delay_seconds": delay,
            "channel": selected_channel,
            "logs": logs
        }
    elif category == FailureCategory.CUSTOMER_ACTIONABLE.value:
        return {
            **state,
            "is_halted": False,
            "recovery_action": RecoveryActionType.SMART_DUNNING.value,
            "recovery_probability": 0.76,
            "retry_delay_seconds": 0,
            "channel": selected_channel,
            "logs": logs
        }
    elif category == FailureCategory.HARD_FAILURE.value:
        return {
            **state,
            "is_halted": False,
            "recovery_action": RecoveryActionType.ALTERNATIVE_PAYMENT.value,
            "recovery_probability": 0.35,
            "retry_delay_seconds": 0,
            "channel": "EMAIL_SMART_LINK",
            "logs": logs
        }
    else:
        return {
            **state,
            "is_halted": False,
            "recovery_action": RecoveryActionType.ESCALATE_MANUAL.value,
            "recovery_probability": 0.15,
            "retry_delay_seconds": 0,
            "channel": "MERCHANT_DESK",
            "logs": logs
        }


# --- 3. Dynamic Negotiation & UPI Intent Dispatch Agent ---
def dispatch_negotiation_agent(state: AgentState) -> AgentState:
    logs = state.get("logs", [])
    if state["is_halted"]:
        return state

    event = state["event"]
    action = state["recovery_action"]
    channel = state.get("channel")
    amount = float(event.get("amount", 0.0))
    p_id = event.get("payment_id", "")
    code = event.get("error_code", "")

    # Evaluate dynamic micro-discount / incentive
    incentive = DynamicIncentiveNegotiator.evaluate_incentive(code, amount)
    final_amt = incentive["adjusted_amount"] if incentive else amount
    
    if incentive:
        logs.append(f"🎁 [Negotiation Agent] Applied 5% friction relief: ₹{amount:.2f} ➔ ₹{final_amt:.2f}")

    # Generate UPI Deep-Link Intent URI
    upi_uri = UPIIntentEngine.generate_upi_uri(p_id, final_amt)
    logs.append(f"⚡ [UPI Intent Engine] Formed 1-tap URI: {upi_uri}")

    # Synthesize tailored message
    if action == RecoveryActionType.SMART_DUNNING.value:
        if incentive:
            msg = (
                f"Hi! We saved your order. Complete payment in 1-tap with an exclusive 5% relief discount "
                f"(Now ₹{final_amt:.2f}): {upi_uri}"
            )
        else:
            msg = f"Your transaction of ₹{final_amt:.2f} failed. Tap here to complete instantly via GPay/PhonePe: {upi_uri}"
    elif action == RecoveryActionType.ALTERNATIVE_PAYMENT.value:
        msg = f"Your card payment could not be processed. Please switch payment method: https://pay.rzp.io/mock/{p_id}"
    else:
        msg = None

    return {
        **state,
        "upi_intent_uri": upi_uri,
        "incentive_data": incentive,
        "dunning_message": msg,
        "logs": logs
    }


# Assemble LangGraph Workflow
def build_recovery_graph():
    wf = StateGraph(AgentState)
    wf.add_node("diagnostic", diagnostic_agent)
    wf.add_node("policy", policy_guardrail_agent)
    wf.add_node("negotiation_dispatch", dispatch_negotiation_agent)

    wf.set_entry_point("diagnostic")
    wf.add_edge("diagnostic", "policy")
    wf.add_edge("policy", "negotiation_dispatch")
    wf.add_edge("negotiation_dispatch", END)
    return wf.compile()

recovery_agent_graph = build_recovery_graph()