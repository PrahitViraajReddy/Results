import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Password ──────────────────────────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"   # 👈 apna password yahan change karo

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f5f3ee;
    color: #1a1a2e;
}
.page-title { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #1a1a2e; margin-bottom: 4px; }
.page-sub   { color: #9090b0; font-size: 0.9rem; margin-bottom: 28px; }
.card {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.05);
    border: 1px solid #e8e4da;
    margin-bottom: 16px;
}
.card-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.5px; color: #9090b0; margin-bottom: 6px; }
.card-value { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #1a1a2e; }
.sec-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.8px;
    color: #9090b0; margin: 20px 0 10px;
}
.stButton > button {
    background: linear-gradient(135deg, #1a1a2e, #2a2a50) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    border: none !important;
}
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #e0dbd0 !important;
    padding: 12px 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False

if not st.session_state.admin_auth:
    st.markdown('<div class="page-title">🛡️ Admin Login</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter password to access the dashboard</div>', unsafe_allow_html=True)

    _, col, _ = st.columns([2, 1, 2])
    with col:
        pwd = st.text_input("", placeholder="Password", type="password", label_visibility="collapsed")
        if st.button("Login", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("❌ Wrong password")
    st.stop()

# ── Load Logs ─────────────────────────────────────────────────────────────────
LOG_FILE = "logs.csv"

st.markdown('<div class="page-title">🛡️ Admin Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Real-time user activity monitor</div>', unsafe_allow_html=True)

col_ref, col_logout = st.columns([8, 1])
with col_ref:
    if st.button("🔄 Refresh"):
        st.rerun()
with col_logout:
    if st.button("Logout"):
        st.session_state.admin_auth = False
        st.rerun()

if not os.path.exists(LOG_FILE):
    st.info("No activity logged yet.")
    st.stop()

logs = pd.read_csv(LOG_FILE)
logs.columns = ["hall_ticket", "page", "timestamp"]
logs["timestamp"] = pd.to_datetime(logs["timestamp"])
logs = logs.sort_values("timestamp", ascending=False).reset_index(drop=True)

# ── Stats Cards ───────────────────────────────────────────────────────────────
total      = len(logs)
unique_ht  = logs["hall_ticket"].nunique()
today      = logs[logs["timestamp"].dt.date == datetime.now().date()]
today_count = len(today)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="card">
        <div class="card-label">Total Searches</div>
        <div class="card-value">{total}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="card">
        <div class="card-label">Unique Users</div>
        <div class="card-value">{unique_ht}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="card">
        <div class="card-label">Today's Searches</div>
        <div class="card-value">{today_count}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    most_used_page = logs["page"].value_counts().idxmax()
    st.markdown(f"""
    <div class="card">
        <div class="card-label">Most Used Page</div>
        <div class="card-value" style="font-size:1.3rem;">{most_used_page}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<div class="sec-label">📊 Page Usage</div>', unsafe_allow_html=True)
    page_counts = logs["page"].value_counts().reset_index()
    page_counts.columns = ["page", "count"]
    fig1 = px.bar(
        page_counts, x="page", y="count",
        color="count",
        color_continuous_scale=["#f0ece4", "#c8a84b", "#1a1a2e"],
        labels={"page": "Page", "count": "Searches"},
        text="count"
    )
    fig1.update_traces(textposition="outside")
    fig1.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
        font=dict(family="DM Sans", color="#1a1a2e"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=300
    )
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with col_r:
    st.markdown('<div class="sec-label">📈 Activity Over Time</div>', unsafe_allow_html=True)
    logs["date"] = logs["timestamp"].dt.date
    daily = logs.groupby("date").size().reset_index(name="count")
    fig2 = px.line(
        daily, x="date", y="count",
        markers=True,
        labels={"date": "Date", "count": "Searches"},
    )
    fig2.update_traces(
        line=dict(color="#c8a84b", width=3),
        marker=dict(size=8, color="#1a1a2e")
    )
    fig2.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
        font=dict(family="DM Sans", color="#1a1a2e"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=300
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Recent Activity Table ─────────────────────────────────────────────────────
st.markdown('<div class="sec-label">🕐 Recent Activity</div>', unsafe_allow_html=True)

st.dataframe(
    logs[["timestamp", "hall_ticket", "page"]].head(50),
    use_container_width=True,
    hide_index=True,
    column_config={
        "timestamp": st.column_config.DatetimeColumn("Time", format="DD/MM/YYYY HH:mm:ss"),
        "hall_ticket": st.column_config.TextColumn("Hall Ticket"),
        "page": st.column_config.TextColumn("Page"),
    }
)

# ── Most Active Users ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">🏆 Most Active Users</div>', unsafe_allow_html=True)
top_users = logs["hall_ticket"].value_counts().head(10).reset_index()
top_users.columns = ["Hall Ticket", "Searches"]
st.dataframe(top_users, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.download_button(
    label="⬇️ Download Full Logs",
    data=logs.to_csv(index=False),
    file_name="logs.csv",
    mime="text/csv"
)
