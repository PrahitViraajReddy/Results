import streamlit as st
import pandas as pd
import plotly.express as px

from academic_analytics import (
    load_academic_data,
    normalize_hall_ticket,
    student_metrics,
    what_if_cgpa,
    project_cgpa,
    rule_based_insights,
    validate_data,
)
from genai_insights import build_ai_prompt, generate_gemini_insight

st.set_page_config(page_title="Academic Intelligence", page_icon="🤖", layout="wide")

@st.cache_data
def get_data():
    return load_academic_data()

df = get_data()
semester_metrics = df.attrs.get("semester_metrics", {})

st.markdown("# 🤖 Academic Intelligence")
st.caption("Verified academic metrics → analytics → optional GenAI interpretation")

tab_student, tab_batch, tab_subject, tab_whatif, tab_ai, tab_quality = st.tabs([
    "🎓 Student Scorecard",
    "📊 Batch Analytics",
    "📚 Subject Difficulty",
    "🎯 What-if CGPA",
    "✨ AI Analyst",
    "🛡️ Data Quality",
])

with tab_student:
    st.subheader("Student Performance Scorecard")
    roll = st.text_input("Hall Ticket Number", placeholder="e.g. 21A01A0501", key="scorecard_roll")
    if roll:
        student = df[df["rollNumber"] == normalize_hall_ticket(roll)].copy()
        if student.empty:
            st.error("No student record found.")
        else:
            m = student_metrics(student, semester_metrics)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("CGPA", f"{m['cgpa']:.2f}" if m["cgpa"] is not None else "—")
            c2.metric("Avg Marks", f"{m['avg_marks']:.1f}")
            c3.metric("Credits", f"{m['credits']:.0f}")
            c4.metric("Backlogs", m["backlogs"])
            c5.metric("Pass Rate", f"{m['pass_rate']:.1f}%")

            st.markdown(f"### {m['name']}")
            st.caption(f"{m['branch']} · {m['roll']}")

            if m["sgpa_rows"]:
                trend = pd.DataFrame(m["sgpa_rows"], columns=["Semester", "SGPA", "Credits"])
                fig = px.line(trend, x="Semester", y="SGPA", markers=True, title="SGPA Trend")
                fig.update_yaxes(range=[0, 10.5])
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            left, right = st.columns(2)
            with left:
                st.markdown("#### 🟢 Strong Subjects")
                for subject, score in m["best_subjects"].items():
                    st.success(f"{subject} — {score:.1f}")
            with right:
                st.markdown("#### 🔴 Improvement Priorities")
                for subject, score in m["weak_subjects"].items():
                    st.warning(f"{subject} — {score:.1f}")

            st.markdown("#### 💡 Deterministic Insights")
            for insight in rule_based_insights(m):
                st.info(insight)

with tab_batch:
    st.subheader("Batch Analytics")
    branch_filter = st.multiselect(
        "Branch filter",
        sorted(df["branch"].dropna().astype(str).unique()),
    )
    batch = df.copy()
    if branch_filter:
        batch = batch[batch["branch"].astype(str).isin(branch_filter)]

    student_rows = []
    for roll_no, group in batch.groupby("rollNumber"):
        try:
            student_rows.append(student_metrics(group, semester_metrics))
        except Exception:
            continue
    students = pd.DataFrame(student_rows)

    if students.empty:
        st.warning("No batch data available for the selected filter.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Students", len(students))
        c2.metric("Average CGPA", f"{students['cgpa'].dropna().mean():.2f}" if students["cgpa"].notna().any() else "—")
        c3.metric("Avg Pass Rate", f"{students['pass_rate'].mean():.1f}%")
        c4.metric("Students With Backlogs", int((students["backlogs"] > 0).sum()))

        b1, b2 = st.columns(2)
        with b1:
            branch_cgpa = students.groupby("branch")["cgpa"].mean().dropna().sort_values(ascending=False).reset_index()
            if not branch_cgpa.empty:
                st.plotly_chart(px.bar(branch_cgpa, x="branch", y="cgpa", title="Average CGPA by Branch"), use_container_width=True, config={"displayModeBar": False})
        with b2:
            grade_dist = batch["grade"].value_counts().reindex(["O","A+","A","B+","B","C","P","F","AB"]).fillna(0).reset_index()
            grade_dist.columns = ["Grade", "Count"]
            st.plotly_chart(px.bar(grade_dist, x="Grade", y="Count", title="Grade Distribution"), use_container_width=True, config={"displayModeBar": False})

        st.markdown("#### Top Performers")
        top = students.dropna(subset=["cgpa"]).sort_values("cgpa", ascending=False).head(10)
        st.dataframe(top[["name", "roll", "branch", "cgpa", "avg_marks", "backlogs"]], use_container_width=True, hide_index=True)

with tab_subject:
    st.subheader("Subject Difficulty Analysis")
    subject_stats = (
        df.assign(passed=df["grade"].isin({"O","A+","A","B+","B","C","P"}))
        .groupby(["subjectCode", "subjectName"], dropna=False)
        .agg(
            avg_marks=("total", "mean"),
            pass_rate=("passed", "mean"),
            attempts=("grade", "size"),
        )
        .reset_index()
    )
    subject_stats["pass_rate"] *= 100
    subject_stats["failure_rate"] = 100 - subject_stats["pass_rate"]
    subject_stats = subject_stats.sort_values(["failure_rate", "attempts"], ascending=[False, False])

    min_attempts = st.slider("Minimum attempts", 1, max(1, int(subject_stats["attempts"].max())), min(5, max(1, int(subject_stats["attempts"].max()))))
    filtered = subject_stats[subject_stats["attempts"] >= min_attempts]

    st.dataframe(
        filtered[["subjectCode","subjectName","avg_marks","pass_rate","failure_rate","attempts"]]
        .rename(columns={"avg_marks":"Avg Marks","pass_rate":"Pass %","failure_rate":"Failure %","attempts":"Attempts"})
        .round(1),
        use_container_width=True,
        hide_index=True,
    )
    hard = filtered.head(10)
    if not hard.empty:
        st.plotly_chart(
            px.bar(hard.sort_values("failure_rate"), x="failure_rate", y="subjectName", orientation="h", title="Highest Failure Rate"),
            use_container_width=True,
            config={"displayModeBar": False},
        )

with tab_whatif:
    st.subheader("🎯 What-if CGPA Calculator")
    a, b = st.columns(2)
    with a:
        current = st.number_input("Current CGPA", min_value=0.0, max_value=10.0, value=7.0, step=0.01)
        completed = st.number_input("Completed Credits", min_value=0.0, value=100.0, step=1.0)
        remaining = st.number_input("Remaining Credits", min_value=0.0, value=20.0, step=1.0)
    with b:
        target = st.number_input("Target Final CGPA", min_value=0.0, max_value=10.0, value=7.5, step=0.01)
        future_sgpa = st.number_input("Planned Future SGPA", min_value=0.0, max_value=10.0, value=8.5, step=0.01)

    required = what_if_cgpa(current, completed, remaining, target)
    projected = project_cgpa(current, completed, remaining, future_sgpa)
    c1, c2 = st.columns(2)
    c1.metric("Required Future SGPA", f"{required:.2f}" if required is not None else "—")
    c2.metric("Projected Final CGPA", f"{projected:.2f}" if projected is not None else "—")

    if required is not None:
        if required > 10:
            st.error("Target is mathematically unreachable with the supplied credits.")
        elif required < 0:
            st.success("Target is already below the current trajectory.")
        else:
            st.info(f"You need an average SGPA of {required:.2f} across the remaining {remaining:.0f} credits.")

with tab_ai:
    st.subheader("✨ AI Academic Analyst")
    st.caption("The LLM receives calculated metrics, not the raw workbook. Numerical calculations remain deterministic.")

    roll_ai = st.text_input("Hall Ticket Number", placeholder="Enter a student Hall Ticket Number", key="ai_roll")
    if roll_ai:
        student = df[df["rollNumber"] == normalize_hall_ticket(roll_ai)].copy()
        if student.empty:
            st.error("No student record found.")
        else:
            m = student_metrics(student, semester_metrics)
            deterministic = rule_based_insights(m)

            with st.expander("Verified metrics sent to AI", expanded=False):
                st.json({
                    "student": m["name"],
                    "branch": m["branch"],
                    "cgpa": m["cgpa"],
                    "average_marks": round(m["avg_marks"], 2),
                    "pass_rate": round(m["pass_rate"], 2),
                    "backlogs": m["backlogs"],
                    "sgpa": [{"semester": s, "sgpa": round(v, 2), "credits": c} for s, v, c in m["sgpa_rows"]],
                })

            for insight in deterministic:
                st.info(insight)

            api_key = st.text_input("Gemini API key (optional; prefer Streamlit Secrets)", type="password", key="gemini_key")
            if st.button("✨ Generate AI Analysis", type="primary"):
                with st.spinner("Generating academic analysis..."):
                    prompt = build_ai_prompt(m, deterministic)
                    result, error = generate_gemini_insight(prompt, api_key=api_key or None)
                if error:
                    st.warning(error)
                    st.caption("The deterministic insights above remain available without an API key.")
                else:
                    st.markdown("### AI Interpretation")
                    st.markdown(result)

with tab_quality:
    st.subheader("🛡️ Data Quality & Validation")
    checks = validate_data(df)
    warnings = [(label, count) for label, count in checks if count]
    st.metric("Validation warnings", len(warnings))
    for label, count in checks:
        if count:
            st.warning(f"{label}: {count}")
        else:
            st.success(f"{label}: 0")
    st.caption(f"{len(df):,} subject records loaded for analytics.")
