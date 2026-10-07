import streamlit as st
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from academic_analytics import student_metrics, what_if_cgpa, project_cgpa

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Results App",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "page" not in st.session_state: st.session_state.page = "Home"

# ── Load your Excel workbook directly here ───────────────────────────────────

@st.cache_data
def load_data():
    xl = pd.ExcelFile("results.xlsx")
    grade_points = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0, "AB": 0}
    sem_sheets = [s for s in xl.sheet_names if s != "Summary"]

    summary = xl.parse("Summary")
    summary["RollNumber"] = summary["RollNumber"].map(normalize_hall_ticket)
    branch_map = dict(zip(summary["RollNumber"], summary["Branch"]))

    rows = []
    semester_metrics = {}
    for sheet in sem_sheets:
        semester = sheet.replace("Sem ", "").strip()
        raw = xl.parse(sheet, header=None)

        # Row 0 = subject headers (merged, forward-filled), row 1 = sub-column labels
        # (Code, Subject Name, Int., Ext., Total, Grade, Cr.), row 2+ = data
        header1 = raw.iloc[0].ffill()
        data = raw.iloc[2:].reset_index(drop=True)

        col = 2  # columns 0,1 are RollNumber, Name
        ncols = raw.shape[1]
        while col < ncols - 1:
            label = str(header1[col])
            if " - " not in label:
                break  # reached SGPA / Sem Credits / Sem Backlogs columns

            code_col, name_col = col, col + 1
            int_col, ext_col, total_col, grade_col, cr_col = col + 2, col + 3, col + 4, col + 5, col + 6

            sub = pd.DataFrame({
                "rollNumber": data[0],
                "name": data[1],
                "semester": semester,
                "subjectCode": data[code_col],
                "subjectName": data[name_col],
                "internal": pd.to_numeric(data[int_col], errors="coerce"),
                "external": pd.to_numeric(data[ext_col], errors="coerce"),
                "total": pd.to_numeric(data[total_col], errors="coerce"),
                "grade": data[grade_col].astype(str).str.strip().str.upper(),
                "credits": pd.to_numeric(data[cr_col], errors="coerce"),
            })
            sub["rollNumber"] = sub["rollNumber"].map(normalize_hall_ticket)
            sub["branch"] = sub["rollNumber"].map(branch_map)
            sub = sub.dropna(subset=["total"])
            rows.append(sub)
            col += 7

        # Preserve semester-level metrics from the workbook when available.
        metric_start = col
        if metric_start < ncols:
            for metric_col in range(metric_start, ncols):
                metric_name = str(header1[metric_col]).strip().lower()
                if metric_name in {"sgpa", "sem credits", "semester credits", "credits", "sem backlogs", "backlogs"}:
                    values = pd.to_numeric(data[metric_col], errors="coerce")
                    for idx, value in values.items():
                        roll = normalize_hall_ticket(data.iloc[idx, 0])
                        if roll and pd.notna(value):
                            semester_metrics[(roll, semester, metric_name)] = value

    result = pd.concat(rows, ignore_index=True)
    result.attrs["semester_metrics"] = semester_metrics
    return result

# Normalize Hall Ticket Numbers so accidental spaces do not cause false "Not Found" errors.
def normalize_hall_ticket(value):
    return "".join(str(value).split()).upper()

df = load_data()

# ── Academic Metric Helpers ───────────────────────────────────────────────────

def get_workbook_sgpa(roll_number, semester, semester_metrics):
    roll = normalize_hall_ticket(roll_number)
    value = semester_metrics.get((roll, str(semester), "sgpa"))
    return float(value) if pd.notna(value) else None


def get_student_cgpa(student_data, semester_metrics, grades_map):
    roll = normalize_hall_ticket(student_data["rollNumber"].iloc[0])
    semester_rows = []

    for sem in sorted(student_data["semester"].unique()):
        sgpa = get_workbook_sgpa(roll, sem, semester_metrics)
        sem_credits = semester_metrics.get((roll, str(sem), "sem credits"))
        if sgpa is None or pd.isna(sem_credits):
            continue
        semester_rows.append((sgpa, float(sem_credits)))

    if semester_rows:
        weighted = sum(sgpa * credits for sgpa, credits in semester_rows)
        credits = sum(credits for _, credits in semester_rows)
        if credits > 0 and len(semester_rows) == len(student_data["semester"].unique()):
            return weighted / credits

    # Fallback when workbook semester metrics are unavailable.
    data = student_data.copy()
    data["grade_point"] = data["grade"].str.strip().str.upper().map(grades_map)
    if data["grade"].isin(["F", "AB"]).any() or data["credits"].sum() <= 0:
        return None
    return (data["grade_point"] * data["credits"]).sum() / data["credits"].sum()


# ── PDF Export Helper ─────────────────────────────────────────────────────────

def generate_result_pdf(name, roll_number, branch, all_semesters, attempted_semesters,
                         student_data, columns, grades_map, cgpa_display, cgpa_sub, semester_metrics=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], fontSize=18,
        textColor=colors.HexColor("#1a1a2e"), spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "SubStyle", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#7070a0"), spaceAfter=10,
    )
    sem_style = ParagraphStyle(
        "SemStyle", parent=styles["Heading2"], fontSize=13,
        textColor=colors.HexColor("#1a1a2e"), spaceBefore=14, spaceAfter=6,
    )
    info_style = ParagraphStyle(
        "InfoStyle", parent=styles["Normal"], fontSize=10.5,
        textColor=colors.HexColor("#1a1a2e"), spaceAfter=2,
    )
    note_style = ParagraphStyle(
        "NoteStyle", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#c06060"), spaceAfter=4,
    )

    elements = []
    elements.append(Paragraph("Academic Results Report", title_style))
    elements.append(Paragraph("Results Portal", sub_style))
    elements.append(Paragraph(f"<b>Name:</b> {name}", info_style))
    elements.append(Paragraph(f"<b>Hall Ticket No.:</b> {roll_number}", info_style))
    elements.append(Paragraph(f"<b>Branch:</b> {branch}", info_style))
    elements.append(Spacer(1, 6))

    header_row = ["Code", "Subject", "Int.", "Ext.", "Total", "Grade", "Cr."]
    col_widths = [22 * mm, 62 * mm, 14 * mm, 14 * mm, 16 * mm, 16 * mm, 14 * mm]

    for sem in all_semesters:
        elements.append(Paragraph(f"Semester {sem}", sem_style))

        if sem not in attempted_semesters:
            elements.append(Paragraph("Not Applied for Exams", note_style))
            elements.append(Spacer(1, 6))
            continue

        sem_df = student_data[student_data["semester"] == sem].reset_index(drop=True)
        table_data = [header_row]
        for _, r in sem_df.iterrows():
            table_data.append([
                str(r["subjectCode"]), str(r["subjectName"]),
                str(r["internal"]), str(r["external"]),
                str(r["total"]), str(r["grade"]), str(r["credits"]),
            ])

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0dbd0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ee")]),
        ]))
        elements.append(t)

        sem_calc = sem_df.copy()
        is_pass = sem_calc["grade"].isin(["O","A+","A","B+","B","C","P"]).all()
        roll_key = normalize_hall_ticket(roll_number)
        workbook_sgpa = None if semester_metrics is None else semester_metrics.get((roll_key, str(sem), "sgpa"))
        if pd.notna(workbook_sgpa):
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"<b>Semester {sem} SGPA: {float(workbook_sgpa):.2f}</b>", info_style))
        else:
            sem_calc["grade_point"] = sem_calc["grade"].map(grades_map)
            total_credits = sem_calc["credits"].sum()
            if is_pass and total_credits > 0:
                sgpa = (sem_calc["grade_point"] * sem_calc["credits"]).sum() / total_credits
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>Semester {sem} SGPA: {sgpa:.2f}</b>", info_style))
            else:
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>Semester {sem}: Backlog(s) present</b>", note_style))

        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Overall CGPA: {cgpa_display}</b> ({cgpa_sub})", sem_style))

    doc.build(elements)
    buf.seek(0)
    return buf

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
        "Comparison": "⚖️  Comparison",
        "Analytics":  "📊  My Analytics",
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
            student_data = df[df["rollNumber"].str.upper() == normalize_hall_ticket(hall_ticket)]
            if student_data.empty:
                st.error("❌ No record found for this Hall Ticket Number")
            else:
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

                grades_map = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'P': 4, 'F': 0, 'AB': 0}
                semester_metrics = df.attrs.get("semester_metrics", {})

                # Track authoritative workbook SGPA/credits for CGPA calculation.
                semester_sgpa_data = []

                # Semester-wise results
                all_semesters = sorted(df["semester"].unique())
                attempted_semesters = set(student_data["semester"].unique())
                for sem in all_semesters:
                    with st.expander(f"📘 Semester {sem}", expanded=True):
                        if sem not in attempted_semesters:
                            st.info("📭 **Not Applied for Exams**")
                            continue

                        sem_df = student_data[
                            student_data["semester"] == sem
                        ].reset_index(drop=True)
                        st.table(sem_df[columns])
                        sem_df = student_data[student_data["semester"] == sem].copy()
                        sem_df["grade"] = sem_df["grade"].str.strip().str.upper()
                        is_pass = sem_df["grade"].isin(["O", "A+", "A", "B+", "B", "C", "P"]).all()
                        total_credits = semester_metrics.get(
                            (normalize_hall_ticket(hall_ticket), str(sem), "sem credits")
                        )
                        if pd.isna(total_credits):
                            total_credits = sem_df["credits"].sum()

                        workbook_sgpa = get_workbook_sgpa(
                            hall_ticket.strip().upper(), sem, semester_metrics
                        )

                        if workbook_sgpa is not None:
                            st.success(f"🎯 **Semester {sem} SGPA: {workbook_sgpa:.2f}**")
                            semester_sgpa_data.append({
                                "sem": sem,
                                "sgpa": workbook_sgpa,
                                "credits": float(total_credits),
                                "passed": is_pass
                            })
                        elif is_pass and total_credits > 0:
                            sem_df["grade_point"] = sem_df["grade"].map(grades_map)
                            sgpa = (sem_df["grade_point"] * sem_df["credits"]).sum() / total_credits
                            st.success(f"🎯 **Semester {sem} SGPA: {sgpa:.2f}**")
                            semester_sgpa_data.append({
                                "sem": sem,
                                "sgpa": sgpa,
                                "credits": float(total_credits),
                                "passed": True
                            })
                        else:
                            semester_sgpa_data.append({
                                "sem": sem,
                                "sgpa": None,
                                "credits": float(total_credits),
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

                # ── Export as PDF ────────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                pdf_buffer = generate_result_pdf(
                    name=name,
                    roll_number=hall_ticket.upper(),
                    branch=branch,
                    all_semesters=all_semesters,
                    attempted_semesters=attempted_semesters,
                    student_data=student_data,
                    columns=columns,
                    grades_map=grades_map,
                    cgpa_display=cgpa_display,
                    cgpa_sub=cgpa_sub,
                    semester_metrics=df.attrs.get("semester_metrics", {}),
                )
                st.download_button(
                    label="📄 Export as PDF",
                    data=pdf_buffer,
                    file_name=f"{hall_ticket.upper()}_result.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )




# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ▸ INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "Comparison":
    import plotly.express as px

    st.markdown('<div class="page-title">⚖️ Compare Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Investigate two students side by side using the same academic metrics used in My Analytics.</div>', unsafe_allow_html=True)

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
        if not ht1.strip():
            errors.append("Student 1 Hall Ticket Number is missing.")
        if not ht2.strip():
            errors.append("Student 2 Hall Ticket Number is missing.")

        d1 = df[df["rollNumber"] == normalize_hall_ticket(ht1)] if ht1.strip() else pd.DataFrame()
        d2 = df[df["rollNumber"] == normalize_hall_ticket(ht2)] if ht2.strip() else pd.DataFrame()

        if ht1.strip() and d1.empty:
            errors.append(f"No record found for **{ht1.upper()}**.")
        if ht2.strip() and d2.empty:
            errors.append(f"No record found for **{ht2.upper()}**.")
        if ht1.strip() and ht2.strip() and normalize_hall_ticket(ht1) == normalize_hall_ticket(ht2):
            errors.append("Please enter two **different** Hall Ticket Numbers.")

        if errors:
            for e in errors:
                st.error(f"❌  {e}")
        else:
            semester_metrics = df.attrs.get("semester_metrics", {})
            name1 = str(d1["name"].iloc[0])
            name2 = str(d2["name"].iloc[0])
            grades_map = {"O":10, "A+":9, "A":8, "B+":7, "B":6, "C":5, "P":4, "F":0, "AB":0}

            cgpa1 = get_student_cgpa(d1, semester_metrics, grades_map)
            cgpa2 = get_student_cgpa(d2, semester_metrics, grades_map)

            def basic_metrics(data, cgpa):
                passed = data["grade"].isin({"O","A+","A","B+","B","C","P"})
                return {
                    "CGPA": cgpa,
                    "Average Marks": data["total"].mean(),
                    "Pass %": passed.mean() * 100 if len(data) else None,
                    "Credits": data["credits"].sum(),
                    "Backlog Records": (~passed).sum()
                }

            m1 = basic_metrics(d1, cgpa1)
            m2 = basic_metrics(d2, cgpa2)

            # ── OVERALL ACADEMIC METRICS ────────────────────────────────────
            st.markdown('<div class="sec-label">📊 Academic Performance Comparison</div>', unsafe_allow_html=True)
            metric_rows = pd.DataFrame([
                {"Metric": "CGPA", name1: m1["CGPA"], name2: m2["CGPA"]},
                {"Metric": "Average Marks", name1: m1["Average Marks"], name2: m2["Average Marks"]},
                {"Metric": "Pass %", name1: m1["Pass %"], name2: m2["Pass %"]},
                {"Metric": "Recorded Credits", name1: m1["Credits"], name2: m2["Credits"]},
                {"Metric": "Backlog Records", name1: m1["Backlog Records"], name2: m2["Backlog Records"]}
            ])
            # Format a separate display table as strings. This avoids pandas
            # dtype conflicts when numeric columns are mixed with formatted text.
            metric_display = pd.DataFrame({
                "Metric": metric_rows["Metric"],
                name1: [
                    f"{m1['CGPA']:.2f}" if pd.notna(m1["CGPA"]) else "—",
                    f"{m1['Average Marks']:.1f}" if pd.notna(m1["Average Marks"]) else "—",
                    f"{m1['Pass %']:.1f}" if pd.notna(m1["Pass %"]) else "—",
                    f"{m1['Credits']:.0f}" if pd.notna(m1["Credits"]) else "—",
                    f"{m1['Backlog Records']:.0f}" if pd.notna(m1["Backlog Records"]) else "—"
                ],
                name2: [
                    f"{m2['CGPA']:.2f}" if pd.notna(m2["CGPA"]) else "—",
                    f"{m2['Average Marks']:.1f}" if pd.notna(m2["Average Marks"]) else "—",
                    f"{m2['Pass %']:.1f}" if pd.notna(m2["Pass %"]) else "—",
                    f"{m2['Credits']:.0f}" if pd.notna(m2["Credits"]) else "—",
                    f"{m2['Backlog Records']:.0f}" if pd.notna(m2["Backlog Records"]) else "—"
                ]
            })
            st.dataframe(metric_display, use_container_width=True, hide_index=True)

            # ── SEMESTER MOVEMENT ───────────────────────────────────────────
            st.markdown('<div class="sec-label">🔎 Semester Movement Comparison</div>', unsafe_allow_html=True)

            def get_sgpa_trend(data):
                result = []
                roll = normalize_hall_ticket(data["rollNumber"].iloc[0])
                for sem in sorted(data["semester"].astype(str).unique()):
                    value = semester_metrics.get((roll, sem, "sgpa"))
                    if pd.notna(value):
                        result.append({"Semester": sem, "SGPA": round(float(value), 2)})
                return result

            def movement_rows(trend):
                rows = []
                previous = None
                for item in trend:
                    sgpa = float(item["SGPA"])
                    rows.append({
                        "Semester": item["Semester"],
                        "SGPA": round(sgpa, 2),
                        "SGPA Δ": None if previous is None else round(sgpa - previous, 2)
                    })
                    previous = sgpa
                return rows

            trend1 = get_sgpa_trend(d1)
            trend2 = get_sgpa_trend(d2)
            movement1 = pd.DataFrame(movement_rows(trend1))
            movement2 = pd.DataFrame(movement_rows(trend2))

            if not movement1.empty or not movement2.empty:
                m1_table = movement1.rename(columns={"SGPA": f"{name1} SGPA", "SGPA Δ": f"{name1} SGPA Δ"})
                m2_table = movement2.rename(columns={"SGPA": f"{name2} SGPA", "SGPA Δ": f"{name2} SGPA Δ"})
                movement_compare = pd.merge(m1_table, m2_table, on="Semester", how="outer").sort_values("Semester")
                if f"{name1} SGPA" in movement_compare.columns and f"{name2} SGPA" in movement_compare.columns:
                    movement_compare["SGPA Gap"] = (
                        movement_compare[f"{name1} SGPA"] - movement_compare[f"{name2} SGPA"]
                    ).round(2)
                st.dataframe(movement_compare, use_container_width=True, hide_index=True)
                st.caption("SGPA Δ = change from the previous semester. SGPA Gap = Student 1 minus Student 2.")

            trend_chart = pd.DataFrame([
                {"Semester": r["Semester"], name1: r["SGPA"], name2: None}
                for r in trend1
            ])
            if trend2:
                for r in trend2:
                    if r["Semester"] in set(trend_chart["Semester"]):
                        trend_chart.loc[trend_chart["Semester"] == r["Semester"], name2] = r["SGPA"]
                    else:
                        trend_chart = pd.concat([trend_chart, pd.DataFrame([{"Semester": r["Semester"], name1: None, name2: r["SGPA"]}])], ignore_index=True)
            if not trend_chart.empty:
                trend_chart = trend_chart.sort_values("Semester")

                # Use long-form data so Plotly receives one consistent numeric
                # SGPA column even when the two students have different semester coverage.
                trend_long = trend_chart.melt(
                    id_vars="Semester",
                    value_vars=[name1, name2],
                    var_name="Student",
                    value_name="SGPA"
                ).dropna(subset=["SGPA"])

                fig = px.line(
                    trend_long,
                    x="Semester",
                    y="SGPA",
                    color="Student",
                    markers=True,
                    title="SGPA Trend Comparison"
                )
                fig.update_layout(
                    paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                    font=dict(family="DM Sans", color="#1a1a2e"),
                    yaxis=dict(range=[0, 10.5], gridcolor="#e8e4da", title="SGPA"),
                    xaxis=dict(gridcolor="#e8e4da", title="Semester"),
                    margin=dict(l=20, r=20, t=50, b=20), height=360
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # ── SEMESTER PERFORMANCE ────────────────────────────────────────
            st.markdown('<div class="sec-label">📚 Semester Performance Comparison</div>', unsafe_allow_html=True)

            def semester_table(data):
                rows = []
                roll = normalize_hall_ticket(data["rollNumber"].iloc[0])
                for sem in sorted(data["semester"].astype(str).unique()):
                    sem_df = data[data["semester"].astype(str) == sem]
                    sgpa = semester_metrics.get((roll, sem, "sgpa"))
                    passed = sem_df["grade"].isin({"O","A+","A","B+","B","C","P"})
                    rows.append({
                        "Semester": sem,
                        "SGPA": round(float(sgpa), 2) if pd.notna(sgpa) else None,
                        "Average Marks": round(float(sem_df["total"].mean()), 1),
                        "Pass %": round(float(passed.mean() * 100), 1) if len(sem_df) else None,
                        "Backlog Records": int((~passed).sum())
                    })
                return pd.DataFrame(rows)

            sem1 = semester_table(d1)
            sem2 = semester_table(d2)
            sem_compare = pd.merge(
                sem1.rename(columns={c: f"{name1} {c}" for c in sem1.columns if c != "Semester"}),
                sem2.rename(columns={c: f"{name2} {c}" for c in sem2.columns if c != "Semester"}),
                on="Semester", how="outer"
            ).sort_values("Semester")
            st.dataframe(sem_compare, use_container_width=True, hide_index=True)

            # ── THEORY VS LAB ───────────────────────────────────────────────
            st.markdown('<div class="sec-label">🧪 Theory vs Lab Comparison</div>', unsafe_allow_html=True)
            practical_codes = {
                "CS106ES", "ME104ES", "PH107BS", "CS108ES", "EN109HS",
                "ME203ES", "CS206ES", "CH207BS", "EE208ES", "CS209ES",
                "AD306PC", "AD307PC", "AD308PC", "AD406PC", "AD407PC",
                "AD409PC", "AD505PC", "AD506PC", "AD507PC", "AD604PC", "AD605PC"
            }

            def course_type(row):
                code = str(row["subjectCode"]).strip().upper()
                name = str(row["subjectName"]).strip().upper()
                return "Lab" if code in practical_codes or "LAB" in name or "LABORATORY" in name else "Theory"

            def type_metrics(data):
                x = data.copy()
                x["Type"] = x.apply(course_type, axis=1)
                result = []
                for typ in ["Theory", "Lab"]:
                    part = x[x["Type"] == typ]
                    result.append({
                        "Course Type": typ,
                        "Internal Avg": part["internal"].mean() if not part.empty else None,
                        "External Avg": part["external"].mean() if not part.empty else None,
                        "Average Total": part["total"].mean() if not part.empty else None
                    })
                return pd.DataFrame(result)

            type1 = type_metrics(d1)
            type2 = type_metrics(d2)
            type_compare = pd.merge(
                type1.rename(columns={c: f"{name1} {c}" for c in type1.columns if c != "Course Type"}),
                type2.rename(columns={c: f"{name2} {c}" for c in type2.columns if c != "Course Type"}),
                on="Course Type", how="outer"
            )
            st.dataframe(type_compare.round(2), use_container_width=True, hide_index=True)

            # ── COMMON SUBJECT ANALYSIS ─────────────────────────────────────
            st.markdown('<div class="sec-label">📖 Common Subject Comparison</div>', unsafe_allow_html=True)
            common = sorted(set(d1["subjectName"]) & set(d2["subjectName"]))
            if common:
                s1 = d1[d1["subjectName"].isin(common)][["subjectName","total","grade"]].rename(columns={"subjectName":"Subject", "total":name1, "grade":f"{name1} Grade"})
                s2 = d2[d2["subjectName"].isin(common)][["subjectName","total","grade"]].rename(columns={"subjectName":"Subject", "total":name2, "grade":f"{name2} Grade"})
                common_df = pd.merge(s1, s2, on="Subject", how="inner")
                common_df["Marks Gap"] = (common_df[name1] - common_df[name2]).round(1)
                st.dataframe(
                    common_df.sort_values("Marks Gap", ascending=False),
                    use_container_width=True, hide_index=True
                )
                chart = common_df.sort_values("Marks Gap", ascending=True).tail(min(12, len(common_df)))
                fig_sub = px.bar(
                    chart, x="Marks Gap", y="Subject", orientation="h",
                    text="Marks Gap", title="Subject-wise Marks Gap (Student 1 − Student 2)"
                )
                fig_sub.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                fig_sub.update_layout(
                    paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                    font=dict(family="DM Sans", color="#1a1a2e"),
                    xaxis=dict(gridcolor="#e8e4da", title="Marks Gap"),
                    yaxis=dict(title="Common Subjects"),
                    margin=dict(l=20, r=40, t=50, b=20), height=max(360, 32 * len(chart))
                )
                st.plotly_chart(fig_sub, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No common subjects are available for comparison.")

            # ── GRADES & BACKLOGS ───────────────────────────────────────────
            st.markdown('<div class="sec-label">🏷️ Grades & Backlogs Comparison</div>', unsafe_allow_html=True)
            grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F", "AB"]
            grade_rows = []
            for grade in grade_order:
                grade_rows.append({
                    "Grade": grade,
                    f"{name1} Records": int((d1["grade"] == grade).sum()),
                    f"{name2} Records": int((d2["grade"] == grade).sum())
                })
            st.dataframe(pd.DataFrame(grade_rows), use_container_width=True, hide_index=True)

            failed1 = d1[d1["grade"].isin({"F","AB"})][["semester","subjectCode","subjectName","grade"]]
            failed2 = d2[d2["grade"].isin({"F","AB"})][["semester","subjectCode","subjectName","grade"]]
            if failed1.empty and failed2.empty:
                st.success("🎉 Neither student has recorded F/AB results in the available data.")
            else:
                b1, b2 = st.columns(2)
                with b1:
                    st.markdown(f'<div class="sec-label">⚠️ {name1} Recorded Backlogs</div>', unsafe_allow_html=True)
                    st.dataframe(
                        failed1.rename(columns={"semester":"Semester","subjectCode":"Code","subjectName":"Subject","grade":"Grade"}),
                        use_container_width=True, hide_index=True
                    )
                with b2:
                    st.markdown(f'<div class="sec-label">⚠️ {name2} Recorded Backlogs</div>', unsafe_allow_html=True)
                    st.dataframe(
                        failed2.rename(columns={"semester":"Semester","subjectCode":"Code","subjectName":"Subject","grade":"Grade"}),
                        use_container_width=True, hide_index=True
                    )

elif st.session_state.page == "Analytics":
    import plotly.express as px

    st.markdown('<div class="page-title">📊 My Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Investigate your academic performance with numbers, trends and scenarios.</div>', unsafe_allow_html=True)

    semester_metrics = df.attrs.get("semester_metrics", {})
    roll = st.text_input(
        "Hall Ticket Number",
        placeholder="Enter Hall Ticket No. e.g. 21A01A0501",
        key="analytics_roll"
    ).strip()

    if not roll:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-title">Explore your academic data</div>
            <div class="empty-desc">Enter your Hall Ticket Number to analyse semesters, subjects, marks, grades and CGPA scenarios.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        normalized = normalize_hall_ticket(roll)
        student = df[df["rollNumber"] == normalized].copy()

        if student.empty:
            st.error("❌ No record found for this Hall Ticket Number.")
        else:
            metrics = student_metrics(student, semester_metrics)

            st.markdown(f"""
            <div class="card">
                <div class="card-label">Student</div>
                <div class="card-value">{metrics["name"]}</div>
                <div class="card-sub">{metrics["roll"]} &nbsp;•&nbsp; {metrics["branch"]}</div>
            </div>
            """, unsafe_allow_html=True)

            tabs = st.tabs([
                "📌 Performance",
                "📚 Semesters",
                "📖 Subjects",
                "🎯 Goals",
                "📝 Internal vs External",
                "🏷️ Grades & Backlogs"
            ])

            # ── PERFORMANCE DASHBOARD ────────────────────────────────────────
            with tabs[0]:
                st.markdown('<div class="sec-label">📌 Performance Dashboard</div>', unsafe_allow_html=True)

                total_records = len(student)
                passed_mask = student["grade"].isin({"O", "A+", "A", "B+", "B", "C", "P"})
                attempted_credits = float(student["credits"].fillna(0).sum())
                earned_credits = float(student.loc[passed_mask, "credits"].fillna(0).sum())
                avg_marks = float(student["total"].mean()) if total_records else 0.0
                grade_point_avg = float(
                    student.assign(_gp=student["grade"].map({
                        "O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6,
                        "C": 5, "P": 4, "F": 0, "AB": 0
                    }))["_gp"].mean()
                ) if total_records else 0.0

                sgpa_values = [row[1] for row in metrics["sgpa_rows"]]
                sgpa_std = float(pd.Series(sgpa_values).std(ddof=0)) if len(sgpa_values) >= 2 else 0.0
                sgpa_range = (max(sgpa_values) - min(sgpa_values)) if sgpa_values else 0.0

                c = st.columns(4)
                dashboard_cards = [
                    ("CGPA", f'{metrics["cgpa"]:.2f}' if metrics["cgpa"] is not None else "—", "Workbook semester SGPA weighted by credits"),
                    ("Average Marks", f"{avg_marks:.1f}", "Mean of recorded subject totals"),
                    ("Grade-point Avg.", f"{grade_point_avg:.2f}", "Mean grade point across records"),
                    ("Pass Rate", f"{metrics["pass_rate"]:.1f}%", "Subject records with passing grade"),
                    ("Recorded Credits", f"{attempted_credits:.0f}", "Credits present in subject records"),
                    ("Passed Credits", f"{earned_credits:.0f}", "Credits attached to passing records"),
                    ("SGPA Volatility", f"{sgpa_std:.2f}", "Population standard deviation across semesters"),
                    ("SGPA Range", f"{sgpa_range:.2f}", "Highest SGPA minus lowest SGPA"),
                ]
                for row_cards, row_data in zip([st.columns(4), st.columns(4)], [dashboard_cards[:4], dashboard_cards[4:]]):
                    for col, (label, value, sub) in zip(row_cards, row_data):
                        with col:
                            st.markdown(
                                f'<div class="card"><div class="card-label">{label}</div>'
                                f'<div class="card-value">{value}</div><div class="card-sub">{sub}</div></div>',
                                unsafe_allow_html=True
                            )

                if metrics["sgpa_rows"]:
                    trend = pd.DataFrame(
                        [{"Semester": sem, "SGPA": sgpa, "Credits": credits}
                         for sem, sgpa, credits in metrics["sgpa_rows"]]
                    )
                    st.markdown('<div class="sec-label">📈 SGPA Trend</div>', unsafe_allow_html=True)
                    fig = px.line(trend, x="Semester", y="SGPA", markers=True, text="SGPA")
                    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
                    fig.update_layout(
                        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                        font=dict(family="DM Sans", color="#1a1a2e"),
                        yaxis=dict(range=[0, 10.5], gridcolor="#e8e4da", title="SGPA"),
                        xaxis=dict(gridcolor="#e8e4da", title="Semester"),
                        margin=dict(l=20, r=20, t=20, b=20), height=360
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                if len(metrics["sgpa_rows"]) >= 2:
                    deltas = []
                    for i, (sem, sgpa, credits) in enumerate(metrics["sgpa_rows"]):
                        previous = metrics["sgpa_rows"][i - 1][1] if i else None
                        deltas.append({
                            "Semester": sem,
                            "SGPA": round(sgpa, 2),
                            "Change vs Previous": None if previous is None else round(sgpa - previous, 2),
                            "Credits": credits,
                            "Weighted Contribution": round((sgpa * credits) / sum(r[2] for r in metrics["sgpa_rows"]), 3)
                        })
                    st.markdown('<div class="sec-label">🔎 Semester Movement</div>', unsafe_allow_html=True)
                    st.dataframe(
                        pd.DataFrame(deltas).rename(columns={
                            "Change vs Previous": "SGPA Δ",
                            "Weighted Contribution": "CGPA Contribution"
                        }),
                        use_container_width=True, hide_index=True
                    )

            # ── SEMESTER ANALYTICS ───────────────────────────────────────────
            with tabs[1]:
                st.markdown('<div class="sec-label">📚 Semester Analytics</div>', unsafe_allow_html=True)

                semester_rows = []
                for sem, sgpa, sem_credits in metrics["sgpa_rows"]:
                    sem_df = student[student["semester"].astype(str) == str(sem)].copy()
                    passed = sem_df["grade"].isin({"O", "A+", "A", "B+", "B", "C", "P"})
                    avg = sem_df["total"].mean() if not sem_df.empty else None
                    semester_rows.append({
                        "Semester": str(sem),
                        "SGPA": round(sgpa, 2),
                        "Credits": round(float(sem_credits), 2),
                        "Average Marks": round(float(avg), 2) if pd.notna(avg) else None,
                        "Pass %": round(float(passed.mean() * 100), 1) if len(sem_df) else None,
                        "F/AB Records": int((~passed).sum()),
                        "CGPA Contribution": round(
                            (sgpa * float(sem_credits)) /
                            sum(r[2] for r in metrics["sgpa_rows"]), 3
                        )
                    })

                if semester_rows:
                    sem_table = pd.DataFrame(semester_rows)
                    st.dataframe(sem_table, use_container_width=True, hide_index=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        fig_s = px.bar(sem_table, x="Semester", y="SGPA", text="SGPA", title="SGPA by Semester")
                        fig_s.update_traces(texttemplate="%{text:.2f}", textposition="outside")
                        fig_s.update_layout(
                            paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                            font=dict(family="DM Sans", color="#1a1a2e"),
                            yaxis=dict(range=[0, 10.5], gridcolor="#e8e4da"),
                            margin=dict(l=20, r=20, t=50, b=20), height=340
                        )
                        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})
                    with col2:
                        fig_m = px.bar(sem_table, x="Semester", y="Average Marks", text="Average Marks", title="Average Marks by Semester")
                        fig_m.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                        fig_m.update_layout(
                            paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                            font=dict(family="DM Sans", color="#1a1a2e"),
                            yaxis=dict(range=[0, 100], gridcolor="#e8e4da"),
                            margin=dict(l=20, r=20, t=50, b=20), height=340
                        )
                        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Semester SGPA records are not available for this student.")

            # ── SUBJECT ANALYTICS ────────────────────────────────────────────
            with tabs[2]:
                st.markdown('<div class="sec-label">📖 Subject Analytics</div>', unsafe_allow_html=True)

                subject_view = student[[
                    "semester", "subjectCode", "subjectName",
                    "internal", "external", "total", "grade", "credits"
                ]].copy()

                subject_view = subject_view.rename(columns={
                    "semester": "Semester",
                    "subjectCode": "Code",
                    "subjectName": "Subject",
                    "internal": "Internal",
                    "external": "External",
                    "total": "Total",
                    "grade": "Grade",
                    "credits": "Credits"
                })

                semesters_available = ["All"] + sorted(
                    subject_view["Semester"].astype(str).unique().tolist()
                )
                selected_sem = st.selectbox(
                    "Filter by semester",
                    semesters_available,
                    key="analytics_subject_sem"
                )
                filtered_subjects = (
                    subject_view if selected_sem == "All"
                    else subject_view[subject_view["Semester"].astype(str) == selected_sem]
                )

                st.dataframe(
                    filtered_subjects.sort_values(["Semester", "Total"], ascending=[True, False]),
                    use_container_width=True, hide_index=True
                )

                if not filtered_subjects.empty:
                    subject_chart = filtered_subjects.sort_values("Total", ascending=True).tail(12)
                    fig_sub = px.bar(
                        subject_chart, x="Total", y="Subject", orientation="h",
                        text="Total", title="Subject Marks"
                    )
                    fig_sub.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig_sub.update_layout(
                        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                        font=dict(family="DM Sans", color="#1a1a2e"),
                        xaxis=dict(range=[0, 105], gridcolor="#e8e4da"),
                        margin=dict(l=20, r=40, t=50, b=20),
                        height=max(360, 34 * len(subject_chart))
                    )
                    st.plotly_chart(fig_sub, use_container_width=True, config={"displayModeBar": False})


            # ── GOAL & SCENARIO ANALYSIS ─────────────────────────────────────
            with tabs[3]:
                st.markdown('<div class="sec-label">🎯 Goal & Scenario Analysis</div>', unsafe_allow_html=True)
                default_cgpa = float(metrics["cgpa"]) if metrics["cgpa"] is not None else 7.0
                default_completed = max(0.0, float(metrics["credits"]))

                c1, c2, c3 = st.columns(3)
                with c1:
                    current_cgpa = st.number_input(
                        "Current CGPA", 0.0, 10.0, min(10.0, max(0.0, default_cgpa)),
                        step=0.01, format="%.2f", key="analytics_current_cgpa"
                    )
                with c2:
                    completed_credits = st.number_input(
                        "Completed Credits", 0.0, value=default_completed,
                        step=1.0, key="analytics_completed_credits"
                    )
                with c3:
                    remaining_credits = st.number_input(
                        "Remaining Credits", 0.0, value=20.0,
                        step=1.0, key="analytics_remaining_credits"
                    )

                if remaining_credits > 0:
                    scenarios = []
                    for future_sgpa in [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]:
                        projected = project_cgpa(
                            current_cgpa, completed_credits,
                            remaining_credits, future_sgpa
                        )
                        scenarios.append({
                            "Future SGPA": future_sgpa,
                            "Projected Final CGPA": round(projected, 3)
                        })

                    st.dataframe(pd.DataFrame(scenarios), use_container_width=True, hide_index=True)

                    fig_goal = px.line(
                        pd.DataFrame(scenarios),
                        x="Future SGPA", y="Projected Final CGPA",
                        markers=True, text="Projected Final CGPA"
                    )
                    fig_goal.update_traces(texttemplate="%{text:.2f}", textposition="top center")
                    fig_goal.update_layout(
                        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                        font=dict(family="DM Sans", color="#1a1a2e"),
                        xaxis=dict(range=[6.8, 10.2], gridcolor="#e8e4da"),
                        yaxis=dict(range=[0, 10.5], gridcolor="#e8e4da"),
                        margin=dict(l=20, r=20, t=20, b=20), height=360
                    )
                    st.plotly_chart(fig_goal, use_container_width=True, config={"displayModeBar": False})

                    target_cgpa = st.number_input(
                        "Target Final CGPA", 0.0, 10.0,
                        min(10.0, max(0.0, default_cgpa + 0.5)),
                        step=0.01, format="%.2f", key="analytics_target_cgpa"
                    )
                    required = what_if_cgpa(
                        current_cgpa, completed_credits,
                        remaining_credits, target_cgpa
                    )
                    if required is not None:
                        if required <= 10:
                            st.success(
                                f"To finish at **{target_cgpa:.2f} CGPA**, the required average future SGPA is **{required:.2f}**."
                            )
                        else:
                            st.error(
                                f"To finish at **{target_cgpa:.2f} CGPA**, the required future SGPA is **{required:.2f}**, which is above the 10.00 maximum."
                            )
                else:
                    st.info("Enter remaining credits greater than 0 to run future scenarios.")

            # ── THEORY VS LAB INTERNAL / EXTERNAL ─────────────────────────────
            with tabs[4]:
                st.markdown('<div class="sec-label">📝 Theory vs Lab Analytics</div>', unsafe_allow_html=True)

                # Classification follows the JNTUH R22 AI & DS course structure.
                # It is based on course identity, not credits, because 0-credit
                # theory and 0-credit lab courses both exist.
                practical_codes = {
                    "CS106ES", "ME104ES", "PH107BS", "CS108ES", "EN109HS",
                    "ME203ES", "CS206ES", "CH207BS", "EE208ES", "CS209ES",
                    "AD306PC", "AD307PC", "AD308PC", "AD309PC",
                    "AD406PC", "AD407PC", "AD409PC",
                    "AD505PC", "AD506PC", "AD507PC",
                    "AD604PC", "AD605PC"
                }

                def course_type(row):
                    code = str(row["subjectCode"]).strip().upper()
                    name = str(row["subjectName"]).strip().upper()
                    if code in practical_codes or "LAB" in name or "LABORATORY" in name:
                        return "Lab"
                    return "Theory"

                ie = student[[
                    "semester", "subjectCode", "subjectName",
                    "internal", "external", "total"
                ]].copy()
                ie["Type"] = ie.apply(course_type, axis=1)

                theory = ie[ie["Type"] == "Theory"]
                lab = ie[ie["Type"] == "Lab"]

                theory_internal = theory["internal"].mean()
                theory_external = theory["external"].mean()
                lab_internal = lab["internal"].mean()
                lab_external = lab["external"].mean()

                c1, c2, c3, c4 = st.columns(4)
                for col, label, value, sub in [
                    (c1, "Theory Internal Avg", theory_internal, "Average internal marks"),
                    (c2, "Theory External Avg", theory_external, "Average external marks"),
                    (c3, "Lab Internal Avg", lab_internal, "Average internal marks"),
                    (c4, "Lab External Avg", lab_external, "Average external marks")
                ]:
                    with col:
                        value_text = "—" if pd.isna(value) else f"{value:.1f}"
                        st.markdown(
                            f'<div class="card"><div class="card-label">{label}</div>'
                            f'<div class="card-value">{value_text}</div><div class="card-sub">{sub}</div></div>',
                            unsafe_allow_html=True
                        )

                comparison = pd.DataFrame({
                    "Course Type": ["Theory", "Lab"],
                    "Internal Average": [theory_internal, lab_internal],
                    "External Average": [theory_external, lab_external]
                })
                st.dataframe(
                    comparison.round(2),
                    use_container_width=True, hide_index=True
                )

                chart_ie = comparison.melt(
                    id_vars="Course Type",
                    value_vars=["Internal Average", "External Average"],
                    var_name="Assessment",
                    value_name="Average Marks"
                ).dropna(subset=["Average Marks"])

                if not chart_ie.empty:
                    fig_ie = px.bar(
                        chart_ie,
                        x="Course Type",
                        y="Average Marks",
                        color="Assessment",
                        barmode="group",
                        text="Average Marks",
                        title="Theory vs Lab: Internal and External Averages"
                    )
                    fig_ie.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                    fig_ie.update_layout(
                        paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                        font=dict(family="DM Sans", color="#1a1a2e"),
                        yaxis=dict(gridcolor="#e8e4da", title="Average Marks"),
                        xaxis=dict(title="Course Type"),
                        yaxis_range=[0, 100],
                        margin=dict(l=20, r=20, t=50, b=40), height=420
                    )
                    st.plotly_chart(fig_ie, use_container_width=True, config={"displayModeBar": False})

                detail = ie.rename(columns={
                    "semester": "Semester",
                    "subjectCode": "Code",
                    "subjectName": "Subject",
                    "internal": "Internal",
                    "external": "External",
                    "total": "Total"
                })
                st.dataframe(
                    detail.sort_values(["Type", "Semester", "Subject"]),
                    use_container_width=True, hide_index=True
                )

            # ── GRADES & BACKLOGS ────────────────────────────────────────────
            with tabs[5]:
                st.markdown('<div class="sec-label">🏷️ Grade & Backlog Analytics</div>', unsafe_allow_html=True)

                grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F", "AB"]
                grade_counts = student["grade"].value_counts().reindex(grade_order, fill_value=0)
                grade_credits = student.groupby("grade")["credits"].sum().reindex(grade_order, fill_value=0)

                grade_table = pd.DataFrame({
                    "Grade": grade_order,
                    "Records": grade_counts.values,
                    "Credits": grade_credits.round(2).values,
                    "Grade Point": [10, 9, 8, 7, 6, 5, 4, 0, 0]
                })
                st.dataframe(grade_table, use_container_width=True, hide_index=True)

                fig_grade = px.bar(
                    grade_table, x="Grade", y="Records", text="Records",
                    title="Grade Distribution"
                )
                fig_grade.update_traces(textposition="outside")
                fig_grade.update_layout(
                    paper_bgcolor="#ffffff", plot_bgcolor="#f5f3ee",
                    font=dict(family="DM Sans", color="#1a1a2e"),
                    yaxis=dict(gridcolor="#e8e4da"),
                    margin=dict(l=20, r=20, t=50, b=20), height=340
                )
                st.plotly_chart(fig_grade, use_container_width=True, config={"displayModeBar": False})

                failed = student[student["grade"].isin({"F", "AB"})].copy()
                if failed.empty:
                    st.success("🎉 No F/AB records found in your results.")
                else:
                    st.markdown('<div class="sec-label">⚠️ Recorded Backlog Details</div>', unsafe_allow_html=True)
                    backlog = failed[[
                        "semester", "subjectCode", "subjectName",
                        "total", "internal", "external", "grade", "credits"
                    ]].rename(columns={
                        "semester": "Semester",
                        "subjectCode": "Code",
                        "subjectName": "Subject",
                        "total": "Total",
                        "internal": "Internal",
                        "external": "External",
                        "grade": "Grade",
                        "credits": "Credits"
                    })
                    st.dataframe(
                        backlog.sort_values(["Semester", "Subject"]),
                        use_container_width=True, hide_index=True
                    )

                    backlog_sem = (
                        failed.groupby("semester")
                        .agg(
                            Backlog_Records=("subjectName", "size"),
                            Backlog_Credits=("credits", "sum")
                        )
                        .reset_index()
                        .rename(columns={"semester": "Semester"})
                    )
                    st.markdown('<div class="sec-label">📍 Backlog Origin by Semester</div>', unsafe_allow_html=True)
                    st.dataframe(backlog_sem, use_container_width=True, hide_index=True)
                    st.caption("Backlog analytics use the F/AB records present in the workbook. A separate repeat-attempt history is not available, so cleared/pending status and true attempt counts are not inferred.")

