import streamlit as st
import pandas as pd

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
    return pd.read_csv("results.csv")   # 👈 replace with your actual CSV file path

df = load_data()

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');

:root {
    --bg:        #070b14;
    --surface:   #0d1526;
    --surface2:  #111d35;
    --border:    #1a2d4a;
    --border2:   #223354;
    --accent:    #00d4ff;
    --accent2:   #0099cc;
    --gold:      #f0b429;
    --gold2:     #d4960a;
    --text:      #e8f0fe;
    --text2:     #7a90b8;
    --text3:     #4a6080;
    --success:   #00c896;
    --danger:    #ff5a6e;
    --warn:      #ffb347;
    --radius:    14px;
    --radius-sm: 9px;
    --shadow:    0 4px 32px rgba(0,0,0,0.45);
    --glow:      0 0 24px rgba(0,212,255,0.12);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ══ Scrollbar ══════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ══ Hide Streamlit chrome ══════════════════════════════════════ */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; }

/* ══ Sidebar ════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }

.sidebar-brand {
    padding: 28px 20px 6px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
.sidebar-icon {
    font-size: 2rem;
    display: block;
    text-align: center;
    margin-bottom: 8px;
}
.sidebar-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--accent) !important;
    text-align: center;
    letter-spacing: 0.5px;
}
.sidebar-tagline {
    font-size: 0.68rem;
    color: var(--text3) !important;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
    padding-bottom: 4px;
}
.sidebar-footer {
    font-size: 0.68rem;
    color: var(--text3) !important;
    text-align: center;
    padding: 16px;
    border-top: 1px solid var(--border);
    margin-top: 20px;
}

/* ══ Nav Buttons ════════════════════════════════════════════════ */
.stButton > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--text2) !important;
    transition: all 0.2s ease !important;
    text-align: left !important;
    padding: 10px 16px !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    border-color: var(--border2) !important;
    transform: none !important;
}

/* ══ Action Buttons (cols) ══════════════════════════════════════ */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
    color: #000 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    padding: 13px 28px !important;
    border-radius: var(--radius) !important;
    text-align: center !important;
    box-shadow: 0 4px 20px rgba(0,212,255,0.25) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(0,212,255,0.4) !important;
    filter: brightness(1.08) !important;
}

/* ══ Text Input ═════════════════════════════════════════════════ */
.stTextInput > div > div > input {
    background: var(--surface2) !important;
    border: 1.5px solid var(--border2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 13px 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text3) !important; }
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
    outline: none !important;
}

/* ══ Cards ══════════════════════════════════════════════════════ */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px 26px;
    margin-bottom: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}
.card:hover { border-color: var(--border2); box-shadow: var(--glow); }
.card:hover::before { opacity: 1; }

.card-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text3);
    margin-bottom: 7px;
    font-weight: 600;
}
.card-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    color: var(--text);
    font-weight: 700;
}
.card-sub { font-size: 0.8rem; color: var(--text3); margin-top: 5px; }

/* ══ Info rows ══════════════════════════════════════════════════ */
.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
}
.info-row:last-child { border-bottom: none; }
.info-key { color: var(--text3); font-size: 0.84rem; font-weight: 500; }
.info-val { color: var(--text); font-weight: 600; font-size: 0.92rem; }

/* ══ Semester badges ════════════════════════════════════════════ */
.sem-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }
.sem-badge {
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: var(--radius-sm);
    padding: 10px 18px;
    text-align: center;
    min-width: 82px;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.sem-badge:hover {
    border-color: var(--accent);
    box-shadow: 0 0 12px rgba(0,212,255,0.15);
}
.sem-badge .s-label {
    font-size: 0.65rem;
    color: var(--text3);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}
.sem-badge .s-val {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text);
    margin-top: 4px;
    font-family: 'Outfit', sans-serif;
}

/* ══ Page headings ══════════════════════════════════════════════ */
.page-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.1rem;
    color: var(--text);
    font-weight: 800;
    margin-bottom: 4px;
    line-height: 1.15;
}
.page-title span { color: var(--accent); }
.page-sub {
    color: var(--text3);
    font-size: 0.88rem;
    margin-bottom: 30px;
    font-weight: 400;
}

/* ══ Section label ══════════════════════════════════════════════ */
.sec-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text3);
    margin: 24px 0 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sec-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ══ Hero ═══════════════════════════════════════════════════════ */
.hero-wrap {
    min-height: 82vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 40px 20px;
    position: relative;
}
.hero-glow {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -60%);
    width: 600px; height: 400px;
    background: radial-gradient(ellipse, rgba(0,212,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: var(--accent);
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.22);
    padding: 6px 18px;
    border-radius: 40px;
    margin-bottom: 28px;
    font-weight: 600;
}
.hero-pill::before { content: '●'; font-size: 0.5rem; animation: pulse-dot 2s infinite; }
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.8rem, 6vw, 4.6rem);
    color: var(--text);
    font-weight: 800;
    line-height: 1.08;
    margin-bottom: 20px;
    letter-spacing: -1px;
}
.hero-title span {
    background: linear-gradient(135deg, var(--accent), #80eaff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-desc {
    font-size: 1.05rem;
    color: var(--text2);
    max-width: 460px;
    margin: 0 auto 48px;
    line-height: 1.8;
    font-weight: 300;
}
.hero-stats {
    display: flex;
    gap: 40px;
    margin-bottom: 48px;
    flex-wrap: wrap;
    justify-content: center;
}
.hero-stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--accent);
}
.hero-stat-label { font-size: 0.75rem; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

/* ══ VS divider ═════════════════════════════════════════════════ */
.vs-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    padding-top: 52px;
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--gold);
    text-shadow: 0 0 20px rgba(240,180,41,0.4);
}

/* ══ Empty state ════════════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 80px 20px;
}
.empty-icon {
    font-size: 3.5rem;
    margin-bottom: 20px;
    filter: grayscale(0.3);
}
.empty-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.9rem;
    color: var(--text);
    font-weight: 800;
    margin-bottom: 10px;
}
.empty-desc {
    color: var(--text3);
    font-size: 0.92rem;
    line-height: 1.8;
    max-width: 380px;
    margin: 0 auto;
}
.empty-badge {
    display: inline-block;
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.2);
    color: var(--accent);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 5px 16px;
    border-radius: 40px;
    margin-bottom: 20px;
}

/* ══ CGPA Card ══════════════════════════════════════════════════ */
.cgpa-card {
    background: linear-gradient(135deg, #0a1628 0%, #0d1e38 50%, #091523 100%);
    border: 1px solid var(--border2);
    border-radius: var(--radius);
    padding: 30px 34px;
    margin-top: 28px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 24px;
}
.cgpa-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--gold), var(--accent));
    background-size: 200%;
    animation: shimmer 3s linear infinite;
}
.cgpa-card::after {
    content: '';
    position: absolute;
    bottom: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,212,255,0.05) 0%, transparent 70%);
    border-radius: 50%;
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
.cgpa-left { flex: 1; min-width: 220px; z-index: 1; }
.cgpa-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 2.5px; color: var(--text3); margin-bottom: 8px; font-weight: 600; }
.cgpa-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: var(--text); margin-bottom: 6px; }
.cgpa-formula { font-size: 0.78rem; color: var(--text3); font-style: italic; }
.cgpa-right { text-align: right; z-index: 1; }
.cgpa-value { font-family: 'Playfair Display', serif; font-size: 3.8rem; font-weight: 800; line-height: 1; }
.cgpa-out-of { font-size: 0.78rem; color: var(--text3); margin-top: 6px; }

/* ══ Alert overrides ════════════════════════════════════════════ */
.stAlert {
    border-radius: var(--radius-sm) !important;
    border: 1px solid !important;
}
div[data-testid="stSuccessMessage"] {
    background: rgba(0,200,150,0.08) !important;
    border-color: rgba(0,200,150,0.3) !important;
    color: var(--success) !important;
}
div[data-testid="stErrorMessage"] {
    background: rgba(255,90,110,0.08) !important;
    border-color: rgba(255,90,110,0.3) !important;
    color: var(--danger) !important;
}
div[data-testid="stWarningMessage"] {
    background: rgba(255,179,71,0.08) !important;
    border-color: rgba(255,179,71,0.3) !important;
    color: var(--warn) !important;
}

/* ══ Expander ═══════════════════════════════════════════════════ */
.streamlit-expander {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 12px !important;
}
.streamlit-expander > div:first-child {
    background: var(--surface2) !important;
    border-radius: var(--radius) !important;
}

/* ══ Table ══════════════════════════════════════════════════════ */
.stTable table {
    background: transparent !important;
    border-collapse: collapse !important;
    width: 100% !important;
}
.stTable th {
    background: var(--surface2) !important;
    color: var(--accent) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    padding: 10px 14px !important;
    border-bottom: 2px solid var(--border2) !important;
    font-weight: 700 !important;
}
.stTable td {
    color: var(--text) !important;
    font-size: 0.88rem !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
}
.stTable tr:hover td {
    background: var(--surface2) !important;
}

/* ══ Divider ════════════════════════════════════════════════════ */
hr {
    border-color: var(--border) !important;
    margin: 16px 0 !important;
}

/* ══ Metric ═════════════════════════════════════════════════════ */
.metric-chip {
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: var(--radius-sm);
    padding: 16px 20px;
    text-align: center;
    transition: all 0.2s;
}
.metric-chip:hover {
    border-color: var(--accent);
    box-shadow: 0 0 14px rgba(0,212,255,0.12);
}
.metric-chip-val {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--accent);
    font-family: 'Playfair Display', serif;
}
.metric-chip-label {
    font-size: 0.65rem;
    color: var(--text3);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 4px;
    font-weight: 600;
}

/* ══ Comparison subject card ════════════════════════════════════ */
.subj-card {
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    margin-bottom: 7px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: opacity 0.2s;
}
.subj-card:hover { opacity: 0.85; }
.subj-name { font-size: 0.86rem; color: var(--text); font-weight: 500; }
.subj-score { font-weight: 800; font-size: 0.95rem; }

/* ══ Gap card ═══════════════════════════════════════════════════ */
.gap-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    margin-bottom: 8px;
}
.gap-card-title { font-weight: 600; color: var(--text); font-size: 0.88rem; }
.gap-badge {
    background: rgba(0,200,150,0.15);
    color: var(--success);
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.76rem;
    font-weight: 700;
    border: 1px solid rgba(0,200,150,0.25);
}
.gap-detail { margin-top: 6px; font-size: 0.8rem; color: var(--text3); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-icon">🎓</span>
        <div class="sidebar-title">Results App</div>
    </div>
    """, unsafe_allow_html=True)

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

    st.markdown('<div class="sidebar-footer">© Prahit Viraaj Reddy Madupu</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "Home":
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-glow"></div>
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
        if st.button("🚀  Get Started", use_container_width=True):
            st.session_state.page = "Results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Results":
    st.markdown('<div class="page-title">📋 Academic <span>Results</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter your Hall Ticket Number to fetch your results</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([3, 1])
    with col_in:
        hall_ticket = st.text_input("", placeholder="Enter Hall Ticket No.  e.g. 23D01A0001", label_visibility="collapsed")
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
                name   = student_data["name"].iloc[0]
                branch = student_data["branch"].iloc[0]

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Student header cards ──
                c1, c2 = st.columns(2)
                c1.markdown(f"""
                <div class="card">
                    <div class="card-label">👤 Student Name</div>
                    <div class="card-value">{name}</div>
                </div>""", unsafe_allow_html=True)
                c2.markdown(f"""
                <div class="card">
                    <div class="card-label">🏫 Branch</div>
                    <div class="card-value">{branch}</div>
                </div>""", unsafe_allow_html=True)

                columns = ["subjectCode","subjectName","internal","external","total","grade","credits"]
                grades_map = {'O':10,'A+':9,'A':8,'B+':7,'B':6,'C':5,'F':0,'Ab':0}
                semester_sgpa_data = []

                semesters = sorted(student_data["semester"].unique())
                for sem in semesters:
                    with st.expander(f"📘 Semester {sem}", expanded=True):
                        sem_df = student_data[student_data["semester"] == sem].reset_index(drop=True)
                        st.table(sem_df[columns])
                        sem_df2 = student_data[student_data["semester"] == sem].copy()

                        # SGPA: show only if ALL subjects in this semester are cleared (no F, no Ab)
                        is_pass = all(sem_df2["grade"] != 'F') and all(sem_df2["grade"] != 'Ab')
                        sem_df2['grade_point'] = sem_df2['grade'].map(grades_map)
                        total_credits = sem_df2['credits'].sum()

                        if is_pass:
                            sgpa = (sem_df2['grade_point'] * sem_df2['credits']).sum() / total_credits
                            st.success(f"🎯 Semester {sem} SGPA: {sgpa:.2f}")
                            semester_sgpa_data.append({"sem": sem, "sgpa": sgpa, "credits": total_credits, "passed": True})
                        else:
                            # Don't show SGPA — just record as failed, no message
                            semester_sgpa_data.append({"sem": sem, "sgpa": None, "credits": total_credits, "passed": False})

                # ── CGPA Block: always show, — if any backlog exists ──
                all_passed = all(s["passed"] for s in semester_sgpa_data)

                if all_passed and semester_sgpa_data:
                    tw = sum(s["sgpa"] * s["credits"] for s in semester_sgpa_data)
                    tc = sum(s["credits"] for s in semester_sgpa_data)
                    cgpa_display = f"{tw/tc:.2f}" if tc > 0 else "—"
                    cgpa_style   = "color: var(--gold);"
                    cgpa_sub     = "out of 10.00"
                else:
                    cgpa_display = "—"
                    cgpa_style   = "color: var(--danger);"
                    cgpa_sub     = "clear all backlogs to unlock CGPA"

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="cgpa-card">
                    <div class="cgpa-left">
                        <div class="cgpa-label">Overall Performance</div>
                        <div class="cgpa-title">Cumulative Grade Point Average</div>
                        <div class="cgpa-formula">CGPA = Σ(Semester SGPA × Credits) ÷ Σ(Total Credits)</div>
                    </div>
                    <div class="cgpa-right">
                        <div class="cgpa-value" style="{cgpa_style}">{cgpa_display}</div>
                        <div class="cgpa-out-of">{cgpa_sub}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Insights":
    import plotly.express as px

    grades_map = {"O":10,"A+":9,"A":8,"B+":7,"B":6,"C":5,"P":4,"F":0,"AB":0}

    st.markdown('<div class="page-title">💡 <span>Insights</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Performance Analytics — Enter your Hall Ticket Number</div>', unsafe_allow_html=True)

    ht = st.text_input("", placeholder="Enter Hall Ticket Number", label_visibility="collapsed", key="insights_ht")

    if ht:
        student = df[df["rollNumber"].str.upper() == ht.upper()].copy()
        if student.empty:
            st.error("❌ Student Not Found")
            st.stop()

        PLOTLY_LAYOUT = dict(
            paper_bgcolor="rgba(13,21,38,0)",
            plot_bgcolor="rgba(13,21,38,0)",
            font=dict(family="Outfit", color="#7a90b8"),
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(color="#7a90b8")),
            yaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(color="#7a90b8")),
            legend=dict(bgcolor="rgba(13,21,38,0.8)", bordercolor="#1a2d4a", borderwidth=1, font=dict(color="#7a90b8")),
        )

        # ── Subject Performance ──
        st.markdown('<div class="sec-label">📊 Subject Performance</div>', unsafe_allow_html=True)
        subject_scores = student.groupby("subjectName")["total"].mean().sort_values(ascending=False)
        fig1 = px.line(x=subject_scores.index, y=subject_scores.values, markers=True,
                       labels={"x":"Subject","y":"Marks"}, height=420)
        fig1.update_traces(
            line=dict(color="#00d4ff", width=3),
            marker=dict(size=10, color="#00d4ff", line=dict(color="#070b14", width=2)),
            hovertemplate="<b>%{x}</b><br>Marks: %{y}<extra></extra>",
            fill="tozeroy", fillcolor="rgba(0,212,255,0.05)"
        )
        fig1.update_xaxes(showticklabels=False)
        fig1.update_layout(**PLOTLY_LAYOUT, dragmode=False)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

        # ── SGPA Progression ──
        st.markdown('<div class="sec-label">📈 SGPA Progression</div>', unsafe_allow_html=True)
        student["grade_point"] = student["grade"].str.strip().map(grades_map)
        sgpa_sem = student.groupby("semester").apply(
            lambda x: (x["grade_point"] * x["credits"]).sum() / x["credits"].sum()
        )
        fig2 = px.line(x=sgpa_sem.index, y=sgpa_sem.values, markers=True,
                       labels={"x":"Semester","y":"SGPA"}, height=380)
        fig2.update_traces(
            line=dict(color="#f0b429", width=3),
            marker=dict(size=10, color="#f0b429", line=dict(color="#070b14", width=2)),
            hovertemplate="<b>Sem %{x}</b><br>SGPA: %{y:.2f}<extra></extra>",
            fill="tozeroy", fillcolor="rgba(240,180,41,0.05)"
        )
        fig2.update_layout(**PLOTLY_LAYOUT, dragmode=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # ── Best & Weak ──
        st.markdown('<div class="sec-label">🏆 Best & Weak Subjects</div>', unsafe_allow_html=True)
        subject_avg = student.groupby("subjectName")["total"].mean().sort_values(ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="font-size:0.78rem;font-weight:700;color:var(--success);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">🟢 Top Subjects</div>', unsafe_allow_html=True)
            for subj, score in subject_avg.head(3).items():
                st.markdown(f"""
                <div class="subj-card" style="background:rgba(0,200,150,0.08);border:1px solid rgba(0,200,150,0.2);">
                    <span class="subj-name">{subj[:32]}</span>
                    <span class="subj-score" style="color:var(--success);">{int(score)}</span>
                </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="font-size:0.78rem;font-weight:700;color:var(--danger);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">🔴 Weak Subjects</div>', unsafe_allow_html=True)
            for subj, score in subject_avg.tail(3).items():
                st.markdown(f"""
                <div class="subj-card" style="background:rgba(255,90,110,0.08);border:1px solid rgba(255,90,110,0.2);">
                    <span class="subj-name">{subj[:32]}</span>
                    <span class="subj-score" style="color:var(--danger);">{int(score)}</span>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Comparison":
    import plotly.graph_objects as go

    st.markdown('<div class="page-title">⚖️ Compare <span>Results</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Enter two Hall Ticket Numbers to compare academic performance side by side</div>', unsafe_allow_html=True)

    col_s1, col_vs, col_s2 = st.columns([5, 1, 5])
    with col_s1:
        st.markdown('<div style="text-align:center;font-weight:700;color:var(--text);margin-bottom:8px;font-size:0.9rem;text-transform:uppercase;letter-spacing:1px;">Student 1</div>', unsafe_allow_html=True)
        ht1 = st.text_input("", placeholder="Hall Ticket No. 1", key="ht1", label_visibility="collapsed")
    with col_vs:
        st.markdown('<div class="vs-wrap">VS</div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown('<div style="text-align:center;font-weight:700;color:var(--text);margin-bottom:8px;font-size:0.9rem;text-transform:uppercase;letter-spacing:1px;">Student 2</div>', unsafe_allow_html=True)
        ht2 = st.text_input("", placeholder="Hall Ticket No. 2", key="ht2", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        compare_btn = st.button("⚖️  Compare Now", use_container_width=True)

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
            grades_map = {'O':10,'A+':9,'A':8,'B+':7,'B':6,'C':5,'P':4,'F':0,'Ab':0}
            name1 = d1["name"].iloc[0]
            name2 = d2["name"].iloc[0]

            PLOTLY_LAYOUT = dict(
                paper_bgcolor="rgba(13,21,38,0)",
                plot_bgcolor="rgba(13,21,38,0)",
                font=dict(family="Outfit", color="#7a90b8"),
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(color="#7a90b8")),
                yaxis=dict(gridcolor="#1a2d4a", linecolor="#1a2d4a", tickfont=dict(color="#7a90b8")),
                legend=dict(bgcolor="rgba(13,21,38,0.8)", bordercolor="#1a2d4a", borderwidth=1, font=dict(color="#e8f0fe")),
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Profile cards ──
            c1, c2 = st.columns(2)

            def make_profile_card(data, name, ht, col):
                d = data.copy()
                d["gp"] = d["grade"].str.strip().map(grades_map)
                passed = all(data["grade"].isin(["O","A+","A","B+","B","C","P"]))
                cgpa_str = f"{(d['gp']*d['credits']).sum()/d['credits'].sum():.2f}" if passed else "—"
                cgpa_color = "var(--gold)" if passed else "var(--danger)"
                col.markdown(f"""
                <div class="card">
                    <div class="card-label">👤 Student</div>
                    <div class="card-value">{name}</div>
                    <div style="margin-top:16px;display:flex;gap:20px;flex-wrap:wrap;">
                        <div class="metric-chip" style="flex:1;min-width:80px;">
                            <div class="metric-chip-val">{int(data['total'].sum())}</div>
                            <div class="metric-chip-label">Total Marks</div>
                        </div>
                        <div class="metric-chip" style="flex:1;min-width:80px;">
                            <div class="metric-chip-val">{int(data['credits'].sum())}</div>
                            <div class="metric-chip-label">Credits</div>
                        </div>
                        <div class="metric-chip" style="flex:1;min-width:80px;">
                            <div class="metric-chip-val" style="color:{cgpa_color};">{cgpa_str}</div>
                            <div class="metric-chip-label">CGPA</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

            make_profile_card(d1, name1, ht1, c1)
            make_profile_card(d2, name2, ht2, c2)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── SGPA Trend ──
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

            t1_data, t2_data = get_sgpa_trend(d1), get_sgpa_trend(d2)
            fig_sgpa = go.Figure()
            if t1_data:
                t1 = pd.DataFrame(t1_data)
                fig_sgpa.add_trace(go.Scatter(
                    x=t1["Semester"], y=t1["SGPA"], mode="lines+markers+text",
                    name=name1, text=t1["SGPA"], textposition="top center",
                    line=dict(color="#00d4ff", width=3),
                    marker=dict(size=10, color="#00d4ff", line=dict(color="#070b14",width=2)),
                    textfont=dict(size=11, color="#00d4ff"),
                    hovertemplate="<b>Sem %{x}</b><br>SGPA: %{y}<extra></extra>"
                ))
            if t2_data:
                t2 = pd.DataFrame(t2_data)
                fig_sgpa.add_trace(go.Scatter(
                    x=t2["Semester"], y=t2["SGPA"], mode="lines+markers+text",
                    name=name2, text=t2["SGPA"], textposition="bottom center",
                    line=dict(color="#f0b429", width=3, dash="dot"),
                    marker=dict(size=10, color="#f0b429", line=dict(color="#070b14",width=2)),
                    textfont=dict(size=11, color="#f0b429"),
                    hovertemplate="<b>Sem %{x}</b><br>SGPA: %{y}<extra></extra>"
                ))
            fig_sgpa.update_layout(**PLOTLY_LAYOUT, yaxis_range=[0, 10.5], height=360)
            st.plotly_chart(fig_sgpa, use_container_width=True, config={"displayModeBar": False})

            # ── Winner Card ──
            st.markdown('<div class="sec-label">🏆 Overall Winner</div>', unsafe_allow_html=True)
            avg1, avg2 = d1["total"].mean(), d2["total"].mean()
            if avg1 > avg2:
                winner, loser, w_avg, l_avg = name1, name2, avg1, avg2
            elif avg2 > avg1:
                winner, loser, w_avg, l_avg = name2, name1, avg2, avg1
            else:
                winner = None

            if winner:
                st.markdown(f"""
                <div class="card" style="border-left:3px solid var(--success);background:rgba(0,200,150,0.05);">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div class="card-label" style="color:var(--success);">🏆 Leading Student</div>
                            <div class="card-value" style="color:var(--success);">{winner}</div>
                            <div class="card-sub">Avg Marks: {w_avg:.1f} &nbsp;·&nbsp; {loser}: {l_avg:.1f}</div>
                        </div>
                        <div style="font-size:3rem;opacity:0.85;">🥇</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card" style="border-left:3px solid var(--gold);">
                    <div class="card-label" style="color:var(--gold);">⚖️ It's a Tie!</div>
                    <div class="card-value">Both students are equal</div>
                    <div class="card-sub">Avg Marks: {avg1:.1f}</div>
                </div>""", unsafe_allow_html=True)

            # ── Best vs Weak ──
            st.markdown('<div class="sec-label">📚 Best vs Weak Subjects</div>', unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)

            def subject_cards(col, data, label, show_top=True):
                avg = data.groupby("subjectName")["total"].mean().sort_values(ascending=not show_top)
                subjects = avg.head(3)
                icon = "🟢" if show_top else "🔴"
                title = "Best" if show_top else "Weak"
                color = "var(--success)" if show_top else "var(--danger)"
                bg = "rgba(0,200,150,0.08)" if show_top else "rgba(255,90,110,0.08)"
                border = "rgba(0,200,150,0.2)" if show_top else "rgba(255,90,110,0.2)"
                col.markdown(f'<div style="font-size:0.72rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">{icon} {title} — {label}</div>', unsafe_allow_html=True)
                for subj, score in subjects.items():
                    col.markdown(f"""
                    <div class="subj-card" style="background:{bg};border:1px solid {border};">
                        <span class="subj-name">{subj[:30]}</span>
                        <span class="subj-score" style="color:{color};">{int(score)}</span>
                    </div>""", unsafe_allow_html=True)

            with col_b1:
                subject_cards(col_b1, d1, name1, show_top=True)
                st.markdown("<br>", unsafe_allow_html=True)
                subject_cards(col_b1, d1, name1, show_top=False)
            with col_b2:
                subject_cards(col_b2, d2, name2, show_top=True)
                st.markdown("<br>", unsafe_allow_html=True)
                subject_cards(col_b2, d2, name2, show_top=False)

            # ── Common Subjects Analysis ──
            common_subjects = set(d1["subjectName"]) & set(d2["subjectName"])
            if common_subjects:
                subj1 = d1[d1["subjectName"].isin(common_subjects)][["subjectName","total"]].rename(columns={"total":name1})
                subj2 = d2[d2["subjectName"].isin(common_subjects)][["subjectName","total"]].rename(columns={"total":name2})
                merged = pd.merge(subj1, subj2, on="subjectName")
                merged["avg"]  = (merged[name1] + merged[name2]) / 2
                merged["diff"] = abs(merged[name1] - merged[name2])

                col_cs, col_cw = st.columns(2)
                with col_cs:
                    st.markdown('<div class="sec-label">🟢 Common Strong Subjects</div>', unsafe_allow_html=True)
                    for _, row in merged.sort_values("avg", ascending=False).head(3).iterrows():
                        st.markdown(f"""
                        <div class="subj-card" style="background:rgba(0,200,150,0.08);border:1px solid rgba(0,200,150,0.2);">
                            <span class="subj-name">{row['subjectName'][:28]}</span>
                            <span class="subj-score" style="color:var(--success);">avg {row['avg']:.0f}</span>
                        </div>""", unsafe_allow_html=True)
                with col_cw:
                    st.markdown('<div class="sec-label">🔴 Common Weak Subjects</div>', unsafe_allow_html=True)
                    for _, row in merged.sort_values("avg").head(3).iterrows():
                        st.markdown(f"""
                        <div class="subj-card" style="background:rgba(255,90,110,0.08);border:1px solid rgba(255,90,110,0.2);">
                            <span class="subj-name">{row['subjectName'][:28]}</span>
                            <span class="subj-score" style="color:var(--danger);">avg {row['avg']:.0f}</span>
                        </div>""", unsafe_allow_html=True)

                st.markdown('<div class="sec-label">⚡ Biggest Performance Gap</div>', unsafe_allow_html=True)
                for _, row in merged.sort_values("diff", ascending=False).head(3).iterrows():
                    leader = name1 if row[name1] > row[name2] else name2
                    st.markdown(f"""
                    <div class="gap-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span class="gap-card-title">{row['subjectName'][:35]}</span>
                            <span class="gap-badge">+{row['diff']:.0f} gap</span>
                        </div>
                        <div class="gap-detail">🏆 {leader}: <b style="color:var(--success);">{int(max(row[name1],row[name2]))}</b> &nbsp;·&nbsp; other: {int(min(row[name1],row[name2]))}</div>
                    </div>""", unsafe_allow_html=True)

            # ── Semester-wise Improvement ──
            st.markdown('<div class="sec-label">📈 Semester-wise Improvement</div>', unsafe_allow_html=True)
            sem1 = d1.groupby("semester")["total"].mean().reset_index().rename(columns={"total":"avg"})
            sem2 = d2.groupby("semester")["total"].mean().reset_index().rename(columns={"total":"avg"})
            fig_imp = go.Figure()
            fig_imp.add_trace(go.Scatter(
                x=sem1["semester"].astype(str), y=sem1["avg"], mode="lines+markers",
                name=name1, line=dict(color="#00d4ff",width=3),
                marker=dict(size=9,color="#00d4ff",line=dict(color="#070b14",width=2)),
                hovertemplate="<b>Sem %{x}</b><br>Avg: %{y:.1f}<extra></extra>"
            ))
            fig_imp.add_trace(go.Scatter(
                x=sem2["semester"].astype(str), y=sem2["avg"], mode="lines+markers",
                name=name2, line=dict(color="#f0b429",width=3,dash="dot"),
                marker=dict(size=9,color="#f0b429",line=dict(color="#070b14",width=2)),
                hovertemplate="<b>Sem %{x}</b><br>Avg: %{y:.1f}<extra></extra>"
            ))
            fig_imp.update_layout(**PLOTLY_LAYOUT, height=340)
            st.plotly_chart(fig_imp, use_container_width=True, config={"displayModeBar": False})
