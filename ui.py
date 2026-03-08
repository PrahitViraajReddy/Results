import streamlit as st
import pandas as pd
import os

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Results App",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "page" not in st.session_state: st.session_state.page = "Home"

# ── Load your CSV directly here ──────────────────────────────────────────────

@st.cache_data
def load_data():
    return pd.read_csv("results.csv")

df = load_data()

# ── Activity Logger ───────────────────────────────────────────────────────────
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1yDTFJ6g0HhC7vA1PT1cfab1VwET467eu0xPW7TGmUQ4"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS = {
    "type": "service_account",
    "project_id": os.environ.get("GOOGLE_PROJECT_ID", ""),
    "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
    "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL", ""),
    "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get("GOOGLE_CLIENT_X509_CERT_URL", "")
}

@st.cache_resource
def get_sheet():
    try:
        creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        print(f"❌ Google Sheets Error: {e}")
        return None

def log_activity(hall_ticket, page):
    try:
        sheet = get_sheet()
        if sheet is None:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([hall_ticket.upper(), page, timestamp])
        print(f"✅ Logged: {hall_ticket} | {page} | {timestamp}")
    except Exception as e:
        print(f"❌ Logging Error: {e}")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f5f3ee;
    color: #1a1a2e;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1a1a2e !important;
    border-right: 1px solid #2e2e50;
}
section[data-testid="stSidebar"] * { color: #c8c8e8 !important; }
.sidebar-logo {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    color: #e8c97e !important;
    margin-bottom: 4px;
    padding: 10px 0 2px 0;
    text-align: center;
}
.sidebar-sub {
    font-size: 0.72rem;
    color: #505080 !important;
    text-align: center;
    margin-bottom: 26px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* ── Nav Buttons ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    border: 1px solid transparent !important;
    font-size: 0.93rem !important;
    cursor: pointer;
    transition: all 0.18s !important;
    text-align: left !important;
    justify-content: flex-start !important;
}

/* ── Action buttons specific ── */
div[data-testid="stHorizontalBlock"] .stButton > button,
.action-btn .stButton > button {
    background: linear-gradient(135deg, #1a1a2e, #2a2a50) !important;
    color: #ffffff !important;
    padding: 13px 30px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    text-align: center !important;
    justify-content: center !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.18) !important;
}

/* ── Cards ── */
.card {
    background: #ffffff;
    border-radius: 16px;
    padding: 26px 28px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.05);
    border: 1px solid #e8e4da;
    margin-bottom: 16px;
}
.card-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.5px; color: #9090b0; margin-bottom: 6px; }
.card-value { font-family: 'DM Serif Display', serif; font-size: 1.5rem; color: #1a1a2e; }
.card-sub   { font-size: 0.82rem; color: #b0b0cc; margin-top: 4px; }

/* ── Info rows ── */
.info-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 13px 0; border-bottom: 1px solid #f0ece4;
}
.info-row:last-child { border-bottom: none; }
.info-key { color: #7070a0; font-size: 0.87rem; }
.info-val { color: #1a1a2e; font-weight: 600; font-size: 0.93rem; }

/* ── Semester badges ── */
.sem-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.sem-badge {
    background: #f5f3ee; border: 1px solid #e0dbd0;
    border-radius: 10px; padding: 10px 20px; text-align: center; min-width: 80px;
}
.sem-badge .s-label { font-size: 0.7rem; color: #9090b0; text-transform: uppercase; letter-spacing: 1px; }
.sem-badge .s-val   { font-size: 1.25rem; font-weight: 700; color: #1a1a2e; margin-top: 3px; }

/* ── Page heading ── */
.page-title { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #1a1a2e; margin-bottom: 4px; }
.page-sub   { color: #9090b0; font-size: 0.9rem; margin-bottom: 28px; }

/* ── Hero ── */
.hero-wrap {
    min-height: 80vh; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; padding: 40px 20px;
}
.hero-pill {
    display: inline-block;
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 3px;
    color: #c8a84b; background: #e8c97e14;
    border: 1px solid #e8c97e44; padding: 5px 18px;
    border-radius: 20px; margin-bottom: 22px;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2.6rem, 6vw, 4.2rem);
    color: #1a1a2e; line-height: 1.12; margin-bottom: 18px;
}
.hero-title span { color: #c8a84b; }
.hero-desc {
    font-size: 1.05rem; color: #6a6a9a;
    max-width: 440px; margin: 0 auto 44px; line-height: 1.75;
}

/* ── VS divider ── */
.vs-wrap {
    display: flex; align-items: center; justify-content: center;
    padding-top: 60px;
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem; color: #c8a84b;
}

/* ── Empty state ── */
.empty-state { text-align: center; padding: 80px 20px; }
.empty-icon  { font-size: 3.5rem; margin-bottom: 16px; }
.empty-title { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: #1a1a2e; margin-bottom: 8px; }
.empty-desc  { color: #9090b0; font-size: 0.92rem; line-height: 1.7; }

/* ── Inputs ── */
.stTextInput > div > div > input {
    border-radius: 10px !important; border: 1.5px solid #e0dbd0 !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.95rem !important;
    padding: 12px 16px !important; background: #ffffff !important; color: #1a1a2e !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c8a84b !important; box-shadow: 0 0 0 3px rgba(200,168,75,0.15) !important;
    outline: none !important;
}

/* ── Section label ── */
.sec-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.8px;
    color: #9090b0; margin: 20px 0 10px;
}

/* ── CGPA Card ── */
.cgpa-card {
    background: linear-gradient(135deg, #1a1a2e, #2a2a50);
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 28px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(26,26,46,0.18);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 20px;
}
.cgpa-left { flex: 1; min-width: 220px; }
.cgpa-label {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 2px;
    color: #9090c0; margin-bottom: 6px;
}
.cgpa-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.15rem; color: #ffffff; margin-bottom: 4px;
}
.cgpa-formula {
    font-size: 0.82rem; color: #9090c0; font-style: italic;
}
.cgpa-right { text-align: right; }
.cgpa-value {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem; color: #e8c97e; line-height: 1;
}
.cgpa-out-of {
    font-size: 0.82rem; color: #9090c0; margin-top: 4px;
}
.cgpa-breakdown {
    background: #ffffff;
    border-radius: 12px;
    padding: 18px 24px;
    border: 1px solid #e8e4da;
    margin-bottom: 28px;
}
.cgpa-breakdown-title {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.8px;
    color: #9090b0; margin-bottom: 12px;
}
.cgpa-sem-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid #f5f3ee; font-size: 0.88rem;
}
.cgpa-sem-row:last-child { border-bottom: none; }
.cgpa-sem-name { color: #6060a0; }
.cgpa-sem-details { color: #9090b0; font-size: 0.78rem; }
.cgpa-sem-sgpa { font-weight: 700; color: #1a1a2e; }

/* ── Mobile Responsive ── */
@media (max-width: 768px) {
    .hero-title { font-size: 2rem !important; }
    .hero-desc  { font-size: 0.92rem !important; }
    .page-title { font-size: 1.5rem !important; }

    .card {
        padding: 16px 14px !important;
        border-radius: 12px !important;
    }
    .card-value { font-size: 1.2rem !important; }

    .cgpa-card {
        flex-direction: column !important;
        padding: 18px 16px !important;
        gap: 12px !important;
    }
    .cgpa-value { font-size: 2.4rem !important; }
    .cgpa-right { text-align: left !important; }

    .sem-badge { min-width: 60px !important; padding: 8px 12px !important; }
    .sem-badge .s-val { font-size: 1rem !important; }

    .info-row { flex-direction: column !important; align-items: flex-start !important; gap: 4px; }

    .stButton > button { font-size: 0.88rem !important; padding: 10px 14px !important; }

    div[data-testid="stHorizontalBlock"] .stButton > button {
        font-size: 0.92rem !important;
        padding: 12px 16px !important;
    }

    .stTextInput > div > div > input {
        font-size: 0.9rem !important;
        padding: 10px 12px !important;
    }

    .vs-wrap { padding-top: 20px !important; font-size: 1.2rem !important; }

    .sec-label { font-size: 0.68rem !important; }

    .empty-state { padding: 40px 10px !important; }
    .empty-title { font-size: 1.4rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🎓 Results App</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Academic Portal</div>', unsafe_allow_html=True)

    nav_pages = {
        "Home":       "🏠  Home",
        "Results":    "📋  Results",
        "Insights":   "💡  Insights",
        "Comparison": "⚖️  Comparison",
    }

    for key, label in nav_pages.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    st.markdown('<p style="font-size:0.72rem;color:#404060;text-align:center;">©  Results Portal</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-pill">Academic Results Portal</div>
        <div class="hero-title">Welcome to<br><span>Results App</span></div>
        <div class="hero-desc">
            Access your academic results instantly. Enter your Hall Ticket
            number to view your scores, track your progress, and compare
            with fellow students.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([2, 1, 2])
    with col_m:
        if st.button("🚀  Start", use_container_width=True):
            st.session_state.page = "Results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Results":
    st.markdown('<div class="page-title">📋 Academic Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter your Hall Ticket Number to fetch your results</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([3, 1])
    with col_in:
        hall_ticket = st.text_input("", placeholder="Enter Hall Ticket No.  e.g. 21A01A0501", label_visibility="collapsed")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Get Result"):
        if hall_ticket.strip() == "":
            st.warning("⚠️ Please enter a valid Hall Ticket Number")
        else:
            student_data = df[df["rollNumber"].str.upper() == hall_ticket.upper()]
            if student_data.empty:
                st.error("❌ No record found for this Hall Ticket Number")
            else:
                log_activity(hall_ticket, "Results")
                # Student information
                name = student_data["name"].iloc[0]
                branch = student_data["branch"].iloc[0]

                st.markdown(f"### 👤 {name}")
                st.caption(f"Branch: {branch}")

                # Columns to display
                columns = [
                    "subjectCode",
                    "subjectName",
                    "internal",
                    "external",
                    "total",
                    "grade",
                    "credits"
                ]

                grades_map = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'F': 0, 'Ab': 0}

                # Track per-semester SGPA for CGPA calculation
                semester_sgpa_data = []

                # Semester-wise results
                semesters = sorted(student_data["semester"].unique())
                for sem in semesters:
                    with st.expander(f"📘 Semester {sem}", expanded=True):
                        sem_df = student_data[
                            student_data["semester"] == sem
                        ].reset_index(drop=True)
                        st.table(sem_df[columns])
                        sem_df = student_data[student_data["semester"] == sem].copy()
                        is_pass = all(sem_df["grade"] != 'F') and all(sem_df["grade"] != 'Ab')
                        sem_df['grade_point'] = sem_df['grade'].map(grades_map)
                        total_credits = sem_df['credits'].sum()

                        if is_pass:
                            sgpa = (sem_df['grade_point'] * sem_df['credits']).sum() / total_credits
                            st.success(f"🎯 **Semester {sem} SGPA: {sgpa:.2f}**")
                            semester_sgpa_data.append({
                                "sem": sem,
                                "sgpa": sgpa,
                                "credits": total_credits,
                                "passed": True
                            })
                        else:
                            semester_sgpa_data.append({
                                "sem": sem,
                                "sgpa": None,
                                "credits": total_credits,
                                "passed": False
                            })

                # ── CGPA Section ──────────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)

                all_sems_passed = all(s["passed"] for s in semester_sgpa_data)

                if all_sems_passed and semester_sgpa_data:
                    total_weighted = sum(s["sgpa"] * s["credits"] for s in semester_sgpa_data)
                    total_credits_all = sum(s["credits"] for s in semester_sgpa_data)
                    cgpa = total_weighted / total_credits_all if total_credits_all > 0 else 0.0
                    cgpa_display = f"{cgpa:.2f}"
                    cgpa_sub = "out of 10.00"
                    cgpa_value_style = "color:#e8c97e;"
                else:
                    cgpa_display = "—"
                    cgpa_sub = "clear all backlogs to unlock CGPA"
                    cgpa_value_style = "color:#c06060;"

                # CGPA main card
                st.markdown(f"""
                <div class="cgpa-card">
                    <div class="cgpa-left">
                        <div class="cgpa-label">Overall Performance</div>
                        <div class="cgpa-title">Cumulative Grade Point Average</div>
                        <div class="cgpa-formula">
                            CGPA = Σ(Semester SGPA × Semester Credits) ÷ Σ(Total Semester Credits)
                        </div>
                    </div>
                    <div class="cgpa-right">
                        <div class="cgpa-value" style="{cgpa_value_style}">{cgpa_display}</div>
                        <div class="cgpa-out-of">{cgpa_sub}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)




# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Insights":

    import plotly.express as px

    grades_map = {
        "O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6,
        "C": 5, "P": 4, "F": 0, "AB": 0
    }

    st.markdown('<div class="page-title">💡 Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Performance Analytics</div>', unsafe_allow_html=True)

    ht = st.text_input("Enter Hall Ticket Number")

    if ht:
        student = df[df["rollNumber"].str.upper() == ht.upper()].copy()

        if student.empty:
            st.error("Student Not Found")
            st.stop()
        log_activity(ht, "Insights")

        # ── Subject Performance ──────────────────────────────────────────
        st.subheader("📊 Subject Performance")

        subject_scores = (
            student.groupby("subjectName")["total"]
            .mean()
            .sort_values(ascending=False)
        )

        fig1 = px.line(
            x=subject_scores.index,
            y=subject_scores.values,
            markers=True,
            labels={"x": "Subject", "y": "Marks"},
            height=450
        )
        fig1.update_xaxes(showticklabels=False)
        fig1.update_layout(dragmode=False)
        fig1.update_traces(
            hovertemplate="<b>%{x}</b><br>Marks: %{y}<extra></extra>"
        )
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        # ── SGPA Progression ─────────────────────────────────────────────
        student["grade_point"] = student["grade"].str.strip().map(grades_map)

        sgpa_sem = (
            student.groupby("semester")
            .apply(lambda x: (x["grade_point"] * x["credits"]).sum() / x["credits"].sum())
        )

        st.subheader("📈 SGPA Progression")

        fig2 = px.line(
            x=sgpa_sem.index,
            y=sgpa_sem.values,
            markers=True,
            labels={"x": "Semester", "y": "SGPA"},
            height=400
        )
        fig2.update_xaxes(showticklabels=False)
        fig2.update_layout(dragmode=False)
        fig2.update_traces(
            hovertemplate="<b>%{x}</b><br>SGPA: %{y}<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # ── Best & Weak Subjects ─────────────────────────────────────────
        st.subheader("🏆 Best & Weak Subjects")

        subject_avg = (
            student.groupby("subjectName")["total"]
            .mean()
            .sort_values(ascending=False)
        )

        best_subjects = subject_avg.head(3)
        weak_subjects = subject_avg.tail(3)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Top Subjects")
            for subject, score in best_subjects.items():
                st.success(f"{subject} — {score:.0f}")

        with col2:
            st.markdown("### Weak Subjects")
            for subject, score in weak_subjects.items():
                st.error(f"{subject} — {score:.0f}")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Comparison":
    import plotly.graph_objects as go
    import plotly.express as px

    st.markdown('<div class="page-title">⚖️ Compare Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter two Hall Ticket Numbers to compare academic performance side by side</div>', unsafe_allow_html=True)

    col_s1, col_vs, col_s2 = st.columns([5, 1, 5])
    with col_s1:
        st.markdown('<div style="text-align:center;font-weight:600;color:#1a1a2e;margin-bottom:4px">Student 1</div>', unsafe_allow_html=True)
        ht1 = st.text_input("", placeholder="Hall Ticket No. 1", key="ht1", label_visibility="collapsed")
    with col_vs:
        st.markdown('<div class="vs-wrap">VS</div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown('<div style="text-align:center;font-weight:600;color:#1a1a2e;margin-bottom:4px">Student 2</div>', unsafe_allow_html=True)
        ht2 = st.text_input("", placeholder="Hall Ticket No. 2", key="ht2", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        compare_btn = st.button("⚖️  Compare", use_container_width=True)

    if compare_btn:
        errors = []
        if not ht1.strip(): errors.append("Student 1 Hall Ticket Number is missing.")
        if not ht2.strip(): errors.append("Student 2 Hall Ticket Number is missing.")

        d1 = df[df["rollNumber"].str.upper() == ht1.strip().upper()] if ht1.strip() else pd.DataFrame()
        d2 = df[df["rollNumber"].str.upper() == ht2.strip().upper()] if ht2.strip() else pd.DataFrame()

        if ht1.strip() and d1.empty: errors.append(f"No record found for **{ht1.upper()}**.")
        if ht2.strip() and d2.empty: errors.append(f"No record found for **{ht2.upper()}**.")
        if ht1.strip() and ht2.strip() and ht1.strip().upper() == ht2.strip().upper():
            errors.append("Please enter two **different** Hall Ticket Numbers.")

        if errors:
            for e in errors:
                st.error(f"❌  {e}")
        else:
            grades_map = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'P': 4, 'F': 0, 'Ab': 0}
            log_activity(ht1 + " vs " + ht2, "Comparison")

            name1 = d1["name"].iloc[0]
            name2 = d2["name"].iloc[0]

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Side by side info cards ───────────────────────────────────
            c1, c2 = st.columns(2)
            with c1:
                total1 = d1["total"].sum()
                credits1 = d1["credits"].sum()
                d1c = d1.copy()
                d1c["gp"] = d1c["grade"].str.strip().map(grades_map)
                passed1 = all(d1["grade"].isin(["O","A+","A","B+","B","C","P"]))
                if passed1:
                    cgpa1 = (d1c["gp"] * d1c["credits"]).sum() / d1c["credits"].sum()
                    cgpa1_str = f"{cgpa1:.2f}"
                else:
                    cgpa1_str = "—"
                st.markdown(f"""
                <div class="card">
                    <div class="card-label">👤 Student 1</div>
                    <div class="card-value">{name1}</div>
                    <div style="margin-top:14px;display:flex;gap:24px;">
                        <div>
                            <div class="card-label">Total Marks</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#1a1a2e;">{int(total1)}</div>
                        </div>
                        <div>
                            <div class="card-label">Credits</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#1a1a2e;">{int(credits1)}</div>
                        </div>
                        <div>
                            <div class="card-label">CGPA</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#c8a84b;">{cgpa1_str}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                total2 = d2["total"].sum()
                credits2 = d2["credits"].sum()
                d2c = d2.copy()
                d2c["gp"] = d2c["grade"].str.strip().map(grades_map)
                passed2 = all(d2["grade"].isin(["O","A+","A","B+","B","C","P"]))
                if passed2:
                    cgpa2 = (d2c["gp"] * d2c["credits"]).sum() / d2c["credits"].sum()
                    cgpa2_str = f"{cgpa2:.2f}"
                else:
                    cgpa2_str = "—"
                st.markdown(f"""
                <div class="card">
                    <div class="card-label">👤 Student 2</div>
                    <div class="card-value">{name2}</div>
                    <div style="margin-top:14px;display:flex;gap:24px;">
                        <div>
                            <div class="card-label">Total Marks</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#1a1a2e;">{int(total2)}</div>
                        </div>
                        <div>
                            <div class="card-label">Credits</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#1a1a2e;">{int(credits2)}</div>
                        </div>
                        <div>
                            <div class="card-label">CGPA</div>
                            <div style="font-weight:700;font-size:1.2rem;color:#c8a84b;">{cgpa2_str}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── SGPA Trend ────────────────────────────────────────────────
            st.markdown('<div class="sec-label">📈 SGPA Trend Comparison</div>', unsafe_allow_html=True)

            def get_sgpa_trend(data):
                result = []
                for sem in sorted(data["semester"].unique()):
                    s = data[data["semester"] == sem].copy()
                    s["gp"] = s["grade"].str.strip().map(grades_map)
                    is_pass = all(s["grade"].str.strip().isin(["O","A+","A","B+","B","C","P"]))
                    if is_pass:
                        sgpa = (s["gp"] * s["credits"]).sum() / s["credits"].sum()
                        result.append({"Semester": str(sem), "SGPA": round(sgpa, 2)})
                return result

            trend1 = get_sgpa_trend(d1)
            trend2 = get_sgpa_trend(d2)

            fig_sgpa = go.Figure()
            if trend1:
                t1 = pd.DataFrame(trend1)
                fig_sgpa.add_trace(go.Scatter(
                    x=t1["Semester"], y=t1["SGPA"],
                    mode="lines+markers+text", name=name1,
                    text=t1["SGPA"], textposition="top center",
                    line=dict(color="#c8a84b", width=3),
                    marker=dict(size=9, color="#c8a84b"),
                    textfont=dict(size=11, color="#c8a84b")
                ))
            if trend2:
                t2 = pd.DataFrame(trend2)
                fig_sgpa.add_trace(go.Scatter(
                    x=t2["Semester"], y=t2["SGPA"],
                    mode="lines+markers+text", name=name2,
                    text=t2["SGPA"], textposition="bottom center",
                    line=dict(color="#1a1a2e", width=3, dash="dot"),
                    marker=dict(size=9, color="#1a1a2e"),
                    textfont=dict(size=11, color="#1a1a2e")
                ))
            fig_sgpa.update_layout(
                paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                font=dict(family="DM Sans", color="#1a1a2e"),
                yaxis=dict(range=[0, 10.5], gridcolor="#e8e4da", title="SGPA"),
                xaxis=dict(gridcolor="#e8e4da", title="Semester"),
                legend=dict(bgcolor="#ffffff", bordercolor="#e8e4da", borderwidth=1),
                margin=dict(l=20, r=20, t=20, b=20),
                height=360
            )
            st.plotly_chart(fig_sgpa, use_container_width=True, config={"displayModeBar": False})

            # ── Winner Card ───────────────────────────────────────────────
            st.markdown('<div class="sec-label">🏆 Overall Winner</div>', unsafe_allow_html=True)

            avg1 = d1["total"].mean()
            avg2 = d2["total"].mean()
            if avg1 > avg2:
                winner, loser, w_avg, l_avg = name1, name2, avg1, avg2
                winner_color = "#2e7d32"; winner_bg = "#e8f5e9"
            elif avg2 > avg1:
                winner, loser, w_avg, l_avg = name2, name1, avg2, avg1
                winner_color = "#2e7d32"; winner_bg = "#e8f5e9"
            else:
                winner = None

            if winner:
                st.markdown(f"""
                <div class="card" style="border-left: 5px solid #2e7d32; background:{winner_bg};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div class="card-label">🏆 Leading Student</div>
                            <div class="card-value" style="color:#2e7d32;">{winner}</div>
                            <div class="card-sub">Avg Marks: {w_avg:.1f} &nbsp;|&nbsp; {loser}: {l_avg:.1f}</div>
                        </div>
                        <div style="font-size:3rem;">🥇</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card" style="border-left:5px solid #c8a84b;">
                    <div class="card-label">⚖️ It's a Tie!</div>
                    <div class="card-value">Both students are equal</div>
                    <div class="card-sub">Avg Marks: {avg1:.1f}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Best & Weak Subjects Side by Side ────────────────────────
            st.markdown('<div class="sec-label">📚 Best vs Weak Subjects</div>', unsafe_allow_html=True)

            col_b1, col_b2 = st.columns(2)

            def subject_cards(data, label, show_top=True):
                avg = data.groupby("subjectName")["total"].mean().sort_values(ascending=not show_top)
                subjects = avg.head(3)
                icon = "🟢" if show_top else "🔴"
                title = "Best" if show_top else "Weak"
                bg = "#e8f5e9" if show_top else "#ffebee"
                color = "#2e7d32" if show_top else "#c62828"
                st.markdown(f'<div style="font-weight:600;color:#1a1a2e;margin-bottom:8px;">{icon} {title} — {label}</div>', unsafe_allow_html=True)
                for subj, score in subjects.items():
                    st.markdown(f"""
                    <div style="background:{bg};border-radius:10px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.88rem;color:#1a1a2e;font-weight:500;">{subj[:30]}</span>
                        <span style="font-weight:700;color:{color};">{int(score)}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with col_b1:
                subject_cards(d1, name1, show_top=True)
                st.markdown("<br>", unsafe_allow_html=True)
                subject_cards(d1, name1, show_top=False)

            with col_b2:
                subject_cards(d2, name2, show_top=True)
                st.markdown("<br>", unsafe_allow_html=True)
                subject_cards(d2, name2, show_top=False)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Common Strong & Weak Subjects ─────────────────────────────
            common_subjects = set(d1["subjectName"]) & set(d2["subjectName"])
            if common_subjects:
                subj1 = d1[d1["subjectName"].isin(common_subjects)][["subjectName","total"]].rename(columns={"total": name1})
                subj2 = d2[d2["subjectName"].isin(common_subjects)][["subjectName","total"]].rename(columns={"total": name2})
                merged = pd.merge(subj1, subj2, on="subjectName")
                merged["avg"] = (merged[name1] + merged[name2]) / 2
                merged["diff"] = abs(merged[name1] - merged[name2])

                common_strong = merged.sort_values("avg", ascending=False).head(3)
                common_weak   = merged.sort_values("avg").head(3)
                most_diff     = merged.sort_values("diff", ascending=False).head(3)

                col_cs, col_cw = st.columns(2)
                with col_cs:
                    st.markdown('<div class="sec-label">🟢 Common Strong Subjects</div>', unsafe_allow_html=True)
                    for _, row in common_strong.iterrows():
                        st.markdown(f"""
                        <div style="background:#e8f5e9;border-radius:10px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;">
                            <span style="font-size:0.88rem;color:#1a1a2e;font-weight:500;">{row['subjectName'][:28]}</span>
                            <span style="color:#2e7d32;font-weight:700;">avg {row['avg']:.0f}</span>
                        </div>
                        """, unsafe_allow_html=True)

                with col_cw:
                    st.markdown('<div class="sec-label">🔴 Common Weak Subjects</div>', unsafe_allow_html=True)
                    for _, row in common_weak.iterrows():
                        st.markdown(f"""
                        <div style="background:#ffebee;border-radius:10px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;">
                            <span style="font-size:0.88rem;color:#1a1a2e;font-weight:500;">{row['subjectName'][:28]}</span>
                            <span style="color:#c62828;font-weight:700;">avg {row['avg']:.0f}</span>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="sec-label">⚡ Biggest Performance Gap</div>', unsafe_allow_html=True)
                for _, row in most_diff.iterrows():
                    leader = name1 if row[name1] > row[name2] else name2
                    leader_score = max(row[name1], row[name2])
                    lagger_score = min(row[name1], row[name2])
                    st.markdown(f"""
                    <div class="card" style="padding:14px 18px;margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-weight:600;color:#1a1a2e;font-size:0.9rem;">{row['subjectName'][:35]}</span>
                            <span style="background:#e8f5e9;color:#2e7d32;padding:2px 10px;border-radius:20px;font-size:0.8rem;font-weight:600;">+{row['diff']:.0f} gap</span>
                        </div>
                        <div style="margin-top:6px;font-size:0.82rem;color:#9090b0;">
                            🏆 {leader}: <b style="color:#2e7d32;">{int(leader_score)}</b> &nbsp;|&nbsp; {int(lagger_score)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Semester-wise Improvement ─────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec-label">📈 Semester-wise Improvement</div>', unsafe_allow_html=True)

            def get_sem_avg(data):
                return data.groupby("semester")["total"].mean().reset_index().rename(columns={"total": "avg"})

            sem1 = get_sem_avg(d1)
            sem2 = get_sem_avg(d2)

            fig_imp = go.Figure()
            fig_imp.add_trace(go.Scatter(
                x=sem1["semester"].astype(str), y=sem1["avg"],
                mode="lines+markers", name=name1,
                line=dict(color="#c8a84b", width=3),
                marker=dict(size=9, color="#c8a84b"),
                hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}<extra></extra>"
            ))
            fig_imp.add_trace(go.Scatter(
                x=sem2["semester"].astype(str), y=sem2["avg"],
                mode="lines+markers", name=name2,
                line=dict(color="#1a1a2e", width=3, dash="dot"),
                marker=dict(size=9, color="#1a1a2e"),
                hovertemplate="<b>%{x}</b><br>Avg: %{y:.1f}<extra></extra>"
            ))
            fig_imp.update_layout(
                paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                font=dict(family="DM Sans", color="#1a1a2e"),
                xaxis=dict(gridcolor="#e8e4da", title="Semester"),
                yaxis=dict(gridcolor="#e8e4da", title="Avg Marks"),
                legend=dict(bgcolor="#ffffff", bordercolor="#e8e4da", borderwidth=1),
                margin=dict(l=20, r=20, t=20, b=20),
                height=340
            )
            st.plotly_chart(fig_imp, use_container_width=True, config={"displayModeBar": False})
