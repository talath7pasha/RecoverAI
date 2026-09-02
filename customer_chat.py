import streamlit as st
import requests
import json
import time

try:
    from db_logger import log_transaction
except ImportError:
    log_transaction = lambda *args, **kwargs: None

st.set_page_config(
    page_title="RecoverAI Assistant",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

API_BASE = "http://127.0.0.1:8000"
ORDER_AMT = 6500.0
ORDER_ID = "pay_live_9821"

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stChatMessage, .stChatMessage p, .stMarkdown, .stMarkdown p {
        color: #f8fafc !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
    }

    .chat-header {
        display: flex;
        align-items: center;
        background-color: #1e293b;
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    .avatar-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #2563eb;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-right: 14px;
    }
    .status-text {
        font-size: 12px;
        color: #22c55e;
        font-weight: 500;
    }
</style>
<div class="chat-header">
    <div class="avatar-icon">⚡</div>
    <div>
        <strong style="font-size: 16px; color: #ffffff;">RecoverAI Multimodal Support Assistant</strong><br/>
        <span class="status-text">● Active • Voice & Code-Switching Channel</span>
    </div>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "text": f"👋 **RecoverAI Alert**\n\nWe noticed your payment of **₹{ORDER_AMT:,.2f}** for Order **#{ORDER_ID}** failed.\n\nHow can I help you resolve this?\n• *Ask in English or Hinglish ('bhai split kardo', 'offers?')*\n• *Send a Voice Note / PTP ('Friday ko pay karunga')*\n• *Compliance Opt-Out ('stop messaging')*"
        }
    ]

for msg in st.session_state.messages:
    avatar = "⚡" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["text"])

# Voice-to-Recovery Simulation Tray
st.markdown("---")
st.markdown("##### 🎙️ Hinglish Voice Note Recovery Simulator")
v_col1, v_col2 = st.columns(2)
with v_col1:
    if st.button("🎤 Voice Note: 'Bhai salary aane ke baad Friday pay karunga'", use_container_width=True):
        transcript = "Bhai salary aane ke baad Friday pay karunga"
        st.session_state.messages.append({"role": "user", "text": f"🎙️ *[Voice Audio Clip]* \"{transcript}\""})
        res = requests.post(f"{API_BASE}/api/v1/conversational-negotiate", json={"payment_id": ORDER_ID, "user_message": transcript, "amount": ORDER_AMT, "customer_tier": "VIP_ENTERPRISE"}).json()
        log_transaction("Voice-Agent", transcript, res["action"], ORDER_AMT, ORDER_AMT, 0.98)
        st.session_state.messages.append({"role": "assistant", "text": res["reply"]})
        st.rerun()

with v_col2:
    if st.button("🎤 Voice Note: 'Paise nahi hai abhi aadha split kardo'", use_container_width=True):
        transcript = "Paise nahi hai abhi aadha split kardo"
        st.session_state.messages.append({"role": "user", "text": f"🎙️ *[Voice Audio Clip]* \"{transcript}\""})
        res = requests.post(f"{API_BASE}/api/v1/conversational-negotiate", json={"payment_id": ORDER_ID, "user_message": transcript, "amount": ORDER_AMT, "customer_tier": "VIP_ENTERPRISE"}).json()
        log_transaction("Voice-Agent", transcript, res["action"], ORDER_AMT, res["adjusted_amount"], 0.95)
        st.session_state.messages.append({"role": "assistant", "text": res["reply"] + f"\n\n👉 [**Complete Part 1 Checkout (₹{res['adjusted_amount']:,.2f}) ↗**]({res['checkout_url']}&split=true)"})
        st.rerun()

# Text Input Box
if prompt := st.chat_input("Type your message (e.g., 'bhai split kardo', 'any offer?')..."):
    st.session_state.messages.append({"role": "user", "text": prompt})
    try:
        res = requests.post(
            f"{API_BASE}/api/v1/conversational-negotiate",
            json={
                "payment_id": ORDER_ID,
                "user_message": prompt,
                "amount": ORDER_AMT,
                "customer_tier": "VIP_ENTERPRISE"
            }
        )
        data = res.json()
        reply_text = data["reply"]

        if data["action"] == "SPLIT_PAY_APPROVED":
            reply_text += f"\n\n👉 [**Complete Part 1 Checkout (₹{data['adjusted_amount']:,.2f}) ↗**]({data['checkout_url']}&split=true)"
        elif data["action"] == "COMPLIANCE_OPTOUT_SUPPRESSED":
            pass
        else:
            reply_text += f"\n\n👉 [**Complete Checkout & Earn Coins ↗**]({data['checkout_url']})"

        log_transaction("Customer-App", prompt, data["action"], ORDER_AMT, data["adjusted_amount"], 0.96)
        st.session_state.messages.append({"role": "assistant", "text": reply_text})
        st.rerun()
    except Exception as e:
        st.error(f"Engine connection failure: {e}")