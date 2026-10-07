import streamlit as st
import pandas as pd
import plotly.express as px

from academic_analytics import load_academic_data, normalize_hall_ticket, student_metrics

st.set_page_config(page_title="Backlog Analytics", page_icon="📌", layout="wide")

@st.cache_data
def get_data():
    return load_academic_data()

df = get_data()
semester_metrics = df.attrs.get("semester_metrics", {})
failed = df[~df["grade"].isin({"O","A+","A","B+","B","C","P"})].copy()

st.markdown("# 📌 Backlog Analytics")
st.caption("Backlog concentration, clearance indicators and subject-level risk analysis")

c1, c2, c3 = st.columns(3)
c1.metric("Backlog Records", len(failed))
c2.metric("Students With Backlogs", int(failed["rollNumber"].nunique()))
c3.metric("Affected Subjects", int(failed["subjectName"].nunique()))

if failed.empty:
    st.success("No F/AB backlog records were found.")
else:
    left, right = st.columns(2)
    with left:
        subject_rate = (
            df.assign(failed=~df["grade"].isin({"O","A+","A","B+","B","C","P"}))
            .groupby(["subjectCode", "subjectName"])
            .agg(attempts=("failed","size"), backlog_count=("failed","sum"))
            .reset_index()
        )
        subject_rate["backlog_rate"] = subject_rate["backlog_count"] / subject_rate["attempts"] * 100
        subject_rate = subject_rate.sort_values("backlog_rate", ascending=False).head(10)
        st.plotly_chart(
            px.bar(subject_rate.sort_values("backlog_rate"), x="backlog_rate", y="subjectName",
                   orientation="h", title="Subjects With Highest Backlog Rate"),
            use_container_width=True, config={"displayModeBar": False},
        )

    with right:
        semester_backlogs = (
            failed.groupby("semester")["rollNumber"].nunique()
            .reset_index(name="Students")
        )
        st.plotly_chart(
            px.bar(semester_backlogs, x="semester", y="Students", title="Students With Backlogs by Semester"),
            use_container_width=True, config={"displayModeBar": False},
        )

    st.subheader("Students With Highest Backlog Counts")
    counts = failed.groupby(["rollNumber", "name", "branch"]).size().reset_index(name="Backlog Records")
    st.dataframe(counts.sort_values("Backlog Records", ascending=False).head(20),
                 use_container_width=True, hide_index=True)

    st.subheader("Backlog Subject Details")
    st.dataframe(
        failed[["rollNumber","name","branch","semester","subjectCode","subjectName","grade"]]
        .sort_values(["rollNumber","semester"]),
        use_container_width=True, hide_index=True,
    )
