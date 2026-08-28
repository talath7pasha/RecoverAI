# dashboard.py
import io
import time
import pandas as pd
import plotly.express as px
import qrcode
import requests
import streamlit as st

st.set_page_config(
    page_title="RecoverAI - Autonomous Revenue Recovery Engine",
    page_icon="💳",
    layout="wide",
)

API_BASE = "http://127.0.0.1:8000"

st.title("💳 RecoverAI: Next-Gen Autonomous Revenue Recovery Agent")
st.markdown("""
**Razorpay Track 3 Innovations:**
- ⚡ **1-Tap UPI Deep-Link Intent Dispatcher** (`GPay / PhonePe / Paytm / CRED`)
- 🧠 **Contextual Multi-Armed Bandit (RL)** Adaptive Channel Optimizer
- 🎁 **Autonomous Dynamic Negotiation Engine** (Friction-based micro-incentives)
""")

# Fetch Top Metrics
try:
    res = requests.get(f"{API_BASE}/metrics", timeout=2)
    data = res.json() if res.status_code == 200 else {}
except Exception:
    data = {}

c1, c2, c3, c4 = st.columns(4)
total_risk = data.get("total_revenue_at_risk_inr", 0.0)
total_rec = data.get("total_revenue_recovered_inr", 0.0)
rec_rate = data.get("recovery_rate_percentage", 0.0)
total_events = data.get("total_events_processed", 0)

c1.metric("Revenue at Risk", f"₹{total_risk:,.2f}")
c2.metric(
    "Revenue Recovered",
    f"₹{total_rec:,.2f}",
    delta=f"{rec_rate}% Recovery Yield",
)
c3.metric("Recovery Yield Rate", f"{rec_rate}%")
c4.metric("Events Diagnosed", total_events)

st.divider()

# Controls: 1-Click Batch Demo & Reset Ledger Buttons
c_btn, c_reset, c_info = st.columns([1.2, 0.8, 2.5])

with c_btn:
    if st.button(
        "🚀 1-Click Judge Demo (Novelty Batch)",
        use_container_width=True,
        type="primary",
    ):
        scenarios = [
            (
                "pay_upi_101",
                "cust_aditi",
                "+919876500001",
                1499.00,
                "GATEWAY_TIMEOUT",
                "Bank gateway timed out during processing",
                0,
            ),
            (
                "pay_neg_102",
                "cust_rahul",
                "+919876500002",
                6500.00,
                "INSUFFICIENT_FUNDS",
                "Account balance insufficient",
                0,
            ),
            (
                "pay_frd_103",
                "cust_fraud",
                None,
                95000.00,
                "SUSPECTED_FRAUD",
                "High risk card velocity flag",
                0,
            ),
            (
                "pay_act_104",
                "cust_sneha",
                "+919876500003",
                3800.00,
                "PAYMENT_AUTHENTICATION_FAILED",
                "OTP timeout on mobile banking",
                0,
            ),
            (
                "pay_max_105",
                "cust_karan",
                "+919876500004",
                2100.00,
                "GATEWAY_ERROR",
                "Repeated terminal connection drop",
                3,
            ),
        ]
        with st.spinner("Multi-Agent Graph Orchestrating Decisions..."):
            for p_id, c_id, ph, amt, err, desc, retries in scenarios:
                requests.post(
                    f"{API_BASE}/webhook/razorpay/payment-failed",
                    json={
                        "event_id": f"evt_{p_id}",
                        "payment_id": p_id,
                        "customer_id": c_id,
                        "customer_email": f"{c_id}@example.com",
                        "customer_phone": ph,
                        "amount": amt,
                        "error_code": err,
                        "error_description": desc,
                        "retry_count": retries,
                    },
                )
                time.sleep(0.1)

            # Auto-settle high-converting recoveries
            requests.post(
                f"{API_BASE}/webhook/razorpay/payment-success",
                json={"payment_id": "pay_upi_101", "amount": 1499.00},
            )
            requests.post(
                f"{API_BASE}/webhook/razorpay/payment-success",
                json={"payment_id": "pay_neg_102", "amount": 6175.00},
            )  # with 5% relief
            requests.post(
                f"{API_BASE}/webhook/razorpay/payment-success",
                json={"payment_id": "pay_act_104", "amount": 3800.00},
            )

        st.success("Batch completed! Check the Multi-Agent telemetry below.")
        st.rerun()

with c_reset:
    if st.button("🔄 Reset Ledger", use_container_width=True):
        try:
            res = requests.post(f"{API_BASE}/reset-ledger", timeout=2)
            if res.status_code == 200:
                st.success("Ledger reset to ₹0.00!")
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Failed to reset ledger")
        except Exception:
            st.error("Backend not reachable on port 8000")

with c_info:
    st.caption(
        "💡 Run the full multi-agent pipeline or clear the audit ledger before recordings/demos."
    )

# Visualizations
logs = data.get("recent_logs", [])
if logs:
    df = pd.DataFrame(logs)
    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.pie(
            df,
            names="failure_category",
            title="Root Cause Diagnosis Split",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig1.update_layout(margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        channel_df = df["channel"].value_counts().reset_index()
        channel_df.columns = ["Channel", "Count"]
        fig2 = px.bar(
            channel_df,
            x="Channel",
            y="Count",
            title="RL Bandit Channel Selection",
            color="Channel",
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        fig2.update_layout(
            margin=dict(t=40, b=10, l=10, r=10), showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Live Decision Audit Table & QR Inspector
st.subheader("📋 Autonomous Decision Audit Ledger & Deep-Link Inspection")
if logs:
    display_cols = [
        "payment_id",
        "failure_category",
        "action_taken",
        "recovery_probability",
        "channel",
        "amount",
        "status",
    ]
    avail_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[avail_cols], use_container_width=True, height=260)

    st.markdown("### ⚡ Live Multi-Agent Action & 1-Tap Recovery Inspector")
    latest = logs[0]
    col_a, col_b, col_c = st.columns([2, 1.2, 1])

    with col_a:
        st.info(
            f"**Target Payment:** `{latest.get('payment_id')}`\n\n**Agent Reasoning:** {latest.get('reasoning')}"
        )
        st.markdown(f"**Selected Channel:** `{latest.get('channel')}`")
        if latest.get("status") == "RECOVERED":
            st.success(
                f"Status: Payment Successfully Recovered (₹{latest.get('amount', 0):,.2f})"
            )
        else:
            st.warning("Status: Awaiting Customer Conversion / Active Dunning")

    amt = latest.get("amount", 0.0)
    p_id = latest.get("payment_id", "pay_demo")
    sample_upi = f"upi://pay?pa=recoverai.merchant@razorpay&pn=RecoverAI&tr={p_id}&am={amt:.2f}&cu=INR"
    web_fallback = f"http://127.0.0.1:8000/pay/{p_id}?amt={amt:.2f}"

    with col_b:
        st.markdown("**Generated UPI Intent URI:**")
        st.code(sample_upi, language="bash")
        st.link_button(
            "🌐 Open Razorpay Checkout Link",
            web_fallback,
            use_container_width=True,
        )

    with col_c:
        st.markdown("**Scan on Phone:**")
        qr = qrcode.make(sample_upi)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf.getvalue(), width=130, caption="1-Tap UPI QR")