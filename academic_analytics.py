import pandas as pd

GRADE_POINTS = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "P": 4, "F": 0, "AB": 0}
PASS_GRADES = {"O", "A+", "A", "B+", "B", "C", "P"}


def normalize_hall_ticket(value):
    return "".join(str(value).split()).upper()


def load_academic_data(path="results.xlsx"):
    """Load the workbook into one normalized subject-level dataframe."""
    xl = pd.ExcelFile(path)
    summary = xl.parse("Summary")
    summary["RollNumber"] = summary["RollNumber"].map(normalize_hall_ticket)
    branch_map = dict(zip(summary["RollNumber"], summary["Branch"]))

    rows = []
    semester_metrics = {}

    for sheet in [s for s in xl.sheet_names if s != "Summary"]:
        semester = sheet.replace("Sem ", "").strip()
        raw = xl.parse(sheet, header=None)
        header1 = raw.iloc[0].ffill()
        data = raw.iloc[2:].reset_index(drop=True)

        col = 2
        ncols = raw.shape[1]
        while col < ncols - 1:
            label = str(header1[col])
            if " - " not in label:
                break

            sub = pd.DataFrame({
                "rollNumber": data[0].map(normalize_hall_ticket),
                "name": data[1],
                "semester": semester,
                "subjectCode": data[col],
                "subjectName": data[col + 1],
                "internal": pd.to_numeric(data[col + 2], errors="coerce"),
                "external": pd.to_numeric(data[col + 3], errors="coerce"),
                "total": pd.to_numeric(data[col + 4], errors="coerce"),
                "grade": data[col + 5].astype(str).str.strip().str.upper(),
                "credits": pd.to_numeric(data[col + 6], errors="coerce"),
            })
            sub["branch"] = sub["rollNumber"].map(branch_map)
            rows.append(sub.dropna(subset=["total"]))
            col += 7

        if col < ncols:
            for metric_col in range(col, ncols):
                metric_name = str(header1[metric_col]).strip().lower()
                if metric_name in {"sgpa", "sem credits", "semester credits", "credits", "sem backlogs", "backlogs"}:
                    values = pd.to_numeric(data[metric_col], errors="coerce")
                    for idx, value in values.items():
                        roll = normalize_hall_ticket(data.iloc[idx, 0])
                        if roll and pd.notna(value):
                            semester_metrics[(roll, semester, metric_name)] = float(value)

    result = pd.concat(rows, ignore_index=True)
    result.attrs["semester_metrics"] = semester_metrics
    return result


def student_metrics(student, semester_metrics):
    roll = normalize_hall_ticket(student["rollNumber"].iloc[0])
    semesters = sorted(student["semester"].unique(), key=lambda x: str(x))
    sgpa_rows = []

    for sem in semesters:
        sgpa = semester_metrics.get((roll, str(sem), "sgpa"))
        credits = semester_metrics.get((roll, str(sem), "sem credits"))
        if sgpa is not None and credits is not None:
            sgpa_rows.append((str(sem), float(sgpa), float(credits)))

    total_credits = float(student["credits"].fillna(0).sum())
    passed = student["grade"].isin(PASS_GRADES)
    pass_rate = float(passed.mean() * 100) if len(student) else 0.0
    backlogs = int((~passed).sum())
    avg_marks = float(student["total"].mean()) if len(student) else 0.0

    cgpa = None
    if sgpa_rows and all(row[2] > 0 for row in sgpa_rows):
        weighted = sum(sgpa * credits for _, sgpa, credits in sgpa_rows)
        credits = sum(credits for _, _, credits in sgpa_rows)
        if credits:
            cgpa = weighted / credits

    subject_avg = student.groupby("subjectName")["total"].mean().sort_values(ascending=False)
    best = subject_avg.head(3)
    weak = subject_avg.tail(3).sort_values()

    best_sem = max(sgpa_rows, key=lambda x: x[1]) if sgpa_rows else None
    weak_sem = min(sgpa_rows, key=lambda x: x[1]) if sgpa_rows else None

    return {
        "roll": roll,
        "name": str(student["name"].iloc[0]),
        "branch": str(student["branch"].iloc[0]),
        "cgpa": cgpa,
        "avg_marks": avg_marks,
        "credits": total_credits,
        "backlogs": backlogs,
        "pass_rate": pass_rate,
        "sgpa_rows": sgpa_rows,
        "best_subjects": best,
        "weak_subjects": weak,
        "best_semester": best_sem,
        "weakest_semester": weak_sem,
    }


def what_if_cgpa(current_cgpa, completed_credits, remaining_credits, target_cgpa):
    if remaining_credits <= 0:
        return None
    return ((target_cgpa * (completed_credits + remaining_credits)) - (current_cgpa * completed_credits)) / remaining_credits


def project_cgpa(current_cgpa, completed_credits, remaining_credits, future_sgpa):
    total = completed_credits + remaining_credits
    if total <= 0:
        return None
    return ((current_cgpa * completed_credits) + (future_sgpa * remaining_credits)) / total


def rule_based_insights(metrics):
    insights = []
    rows = metrics["sgpa_rows"]

    if metrics["cgpa"] is not None:
        insights.append(f"Current calculated CGPA is {metrics['cgpa']:.2f} across {len(rows)} semester records.")

    if rows:
        best = metrics["best_semester"]
        weak = metrics["weakest_semester"]
        insights.append(f"Strongest semester: Semester {best[0]} with SGPA {best[1]:.2f}.")
        if weak[0] != best[0]:
            insights.append(f"Lowest semester performance: Semester {weak[0]} with SGPA {weak[1]:.2f}.")

        if len(rows) >= 2:
            delta = rows[-1][1] - rows[0][1]
            direction = "improved" if delta > 0 else "declined" if delta < 0 else "remained stable"
            insights.append(f"SGPA has {direction} by {abs(delta):.2f} from the first recorded semester to the latest.")

    if metrics["backlogs"]:
        insights.append(f"{metrics['backlogs']} subject record(s) are currently marked as F/AB.")
    else:
        insights.append("No F/AB subject records were found in the loaded academic data.")

    if not metrics["weak_subjects"].empty:
        subject = metrics["weak_subjects"].index[0]
        score = metrics["weak_subjects"].iloc[0]
        insights.append(f"Lowest average subject score: {subject} ({score:.1f}).")

    return insights


def validate_data(df):
    checks = []
    checks.append(("Missing roll numbers", int(df["rollNumber"].isna().sum())))
    checks.append(("Missing names", int(df["name"].isna().sum())))
    checks.append(("Missing subject names", int(df["subjectName"].isna().sum())))
    checks.append(("Missing grades", int(df["grade"].isin(["", "NAN", "NONE"]).sum())))
    checks.append(("Invalid grades", int((~df["grade"].isin(set(GRADE_POINTS))).sum())))
    checks.append(("Missing/invalid credits", int((df["credits"].isna() | (df["credits"] <= 0)).sum())))
    checks.append(("Marks outside 0-100", int((df["total"].notna() & ((df["total"] < 0) | (df["total"] > 100))).sum())))
    checks.append(("Duplicate subject records", int(df.duplicated(["rollNumber", "semester", "subjectCode"], keep=False).sum())))
    return checks
