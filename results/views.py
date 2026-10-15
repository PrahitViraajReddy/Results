import html
import io
import os
import time
from functools import lru_cache

import pandas as pd
from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from academic_analytics import (
    GRADE_POINTS, PASS_GRADES, load_academic_data, student_metrics, semester_sort_key,
    what_if_cgpa, project_cgpa, rule_based_insights,
)

WORKBOOK = os.environ.get("RESULTS_WORKBOOK", str(settings.BASE_DIR / "results.xlsx"))


@lru_cache(maxsize=1)
def dataset():
    frame = load_academic_data(WORKBOOK)
    metrics = dict(frame.attrs.get("semester_metrics", {}))
    return frame, metrics


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value, digits=2):
    return "—" if value is None or pd.isna(value) else f"{float(value):.{digits}f}"


def student_summary(frame, metrics):
    result = student_metrics(frame, metrics)
    # Keep the original rule: F/AB locks CGPA; otherwise use workbook SGPA ×
    # semester credits when complete, then the grade-point fallback.
    if result["backlogs"] > 0:
        result["cgpa"] = None
    else:
        semesters = frame["semester"].astype(str).unique().tolist()
        roll = str(frame["rollNumber"].iloc[0]).strip().upper()
        semester_rows = []
        for sem in semesters:
            sgpa = metrics.get((roll, str(sem), "sgpa"))
            credits = metrics.get((roll, str(sem), "sem credits"))
            if sgpa is not None and pd.notna(sgpa) and credits is not None and pd.notna(credits):
                semester_rows.append((float(sgpa), float(credits)))
        if semester_rows and len(semester_rows) == len(semesters) and all(cr > 0 for _, cr in semester_rows):
            total_credits = sum(cr for _, cr in semester_rows)
            result["cgpa"] = sum(sgpa * cr for sgpa, cr in semester_rows) / total_credits if total_credits else None
        else:
            grade_points = frame["grade"].astype(str).str.strip().str.upper().map(GRADE_POINTS)
            credits = pd.to_numeric(frame["credits"], errors="coerce").fillna(0)
            result["cgpa"] = ((grade_points * credits).sum() / credits.sum()
                              if credits.sum() > 0 and not frame["grade"].isin(["F", "AB"]).any()
                              else None)
    result["cgpa_display"] = fmt(result["cgpa"])
    result["avg_display"] = fmt(result["avg_marks"], 1)
    result["credits_display"] = fmt(result["credits"], 0)
    result["pass_display"] = fmt(result["pass_rate"], 1) + "%"
    result["insights"] = rule_based_insights(result)
    result["semester_rows"] = [
        {"semester": row[0], "sgpa": fmt(row[1]), "credits": fmt(row[2], 0)}
        for row in result["sgpa_rows"]
    ]
    result["best_subject_rows"] = [
        {"subject": str(k), "marks": fmt(v, 1)}
        for k, v in result["best_subjects"].items()
    ]
    result["weak_subject_rows"] = [
        {"subject": str(k), "marks": fmt(v, 1)}
        for k, v in result["weak_subjects"].items()
    ]
    return result


PRACTICAL_CODES = {
    "CS106ES", "ME104ES", "PH107BS", "CS108ES", "EN109HS", "ME203ES",
    "CS206ES", "CH207BS", "EE208ES", "CS209ES", "AD306PC", "AD307PC",
    "AD308PC", "AD309PC", "AD406PC", "AD407PC", "AD409PC", "AD505PC",
    "AD506PC", "AD507PC", "AD604PC", "AD605PC",
}


def course_type(row):
    code = str(row.get("subjectCode", "")).strip().upper()
    name = str(row.get("subjectName", "")).strip().upper()
    return "Lab" if code in PRACTICAL_CODES or "LAB" in name or "LABORATORY" in name else "Theory"


def extended_academic_views(student):
    data = student.copy()
    data["courseType"] = data.apply(course_type, axis=1)
    type_rows = []
    for label in ("Theory", "Lab"):
        part = data[data["courseType"] == label]
        type_rows.append({
            "type": label,
            "internal": fmt(part["internal"].mean(), 1) if not part.empty else "—",
            "external": fmt(part["external"].mean(), 1) if not part.empty else "—",
            "total": fmt(part["total"].mean(), 1) if not part.empty else "—",
            "count": len(part),
        })
    grade_order = ["O", "A+", "A", "B+", "B", "C", "P", "F", "AB"]
    grade_rows = [{"grade": grade, "count": int((data["grade"] == grade).sum())} for grade in grade_order]
    semester_rows = []
    for sem in sorted(data["semester"].astype(str).unique(), key=lambda x: tuple(int(p) if p.isdigit() else p for p in x.replace("_", "-").split("-"))):
        part = data[data["semester"].astype(str) == sem]
        passed = part["grade"].isin(PASS_GRADES)
        semester_rows.append({
            "semester": sem,
            "average": fmt(part["total"].mean(), 1),
            "pass_rate": fmt(passed.mean() * 100, 1) + "%",
            "backlogs": int((~passed).sum()),
        })
    return {"theory_lab": type_rows, "grade_counts": grade_rows, "semester_performance": semester_rows}


def sgpa_movement(student, metrics):
    roll = str(student["rollNumber"].iloc[0]).strip().upper()
    semesters = sorted(student["semester"].astype(str).unique(), key=semester_sort_key)
    rows = []
    previous = None
    for sem in semesters:
        value = metrics.get((roll, sem, "sgpa"))
        if value is None or pd.isna(value):
            continue
        delta = None
        if previous is not None:
            a = semester_sort_key(previous["semester"])
            b = semester_sort_key(sem)
            consecutive = ((a[0] == b[0] and b[1] == a[1] + 1)
                           or (b[0] == a[0] + 1 and a[1] == 2 and b[1] == 1))
            if consecutive:
                delta = round(float(value) - previous["sgpa"], 2)
        rows.append({"semester": sem, "sgpa": round(float(value), 2),
                     "movement": "—" if delta is None else f"{delta:+.2f}"})
        previous = {"semester": sem, "sgpa": float(value)}
    return rows


def make_pdf(summary, rows, metrics):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, topMargin=18*mm, bottomMargin=18*mm,
                            leftMargin=16*mm, rightMargin=16*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ResultTitle", parent=styles["Title"], fontSize=18,
                           textColor=colors.HexColor("#1a1a2e"), spaceAfter=8)
    normal = ParagraphStyle("ResultNormal", parent=styles["Normal"], fontSize=9)
    story = [
        Paragraph("Academic Results Report", title),
        Paragraph(f"<b>Name:</b> {summary['name']}", normal),
        Paragraph(f"<b>Hall Ticket No.:</b> {summary['roll']}", normal),
        Paragraph(f"<b>Branch:</b> {summary['branch']}", normal),
        Paragraph(f"<b>Overall CGPA:</b> {summary['cgpa_display']}", normal),
        Spacer(1, 10),
    ]
    attempted = set(rows["semester"].astype(str).unique())
    all_semesters = summary.get("all_semesters", sorted(attempted))
    for semester in sorted([str(s) for s in all_semesters], key=lambda s: tuple(int(x) if x.isdigit() else x for x in s.replace("_","-").split("-"))):
        story.append(Paragraph(f"Semester {html.escape(semester)}", styles["Heading2"]))
        if semester not in attempted:
            story.append(Paragraph("Not Applied for Exams", normal))
            story.append(Spacer(1, 6))
            continue
        sem = rows[rows["semester"].astype(str) == semester]
        table_data = [["Code", "Subject", "Internal", "External", "Total", "Grade", "Credits"]]
        for _, item in sem.iterrows():
            table_data.append([str(item["subjectCode"]), html.escape(str(item["subjectName"])),
                fmt(item["internal"], 1), fmt(item["external"], 1), fmt(item["total"], 1),
                str(item["grade"]), fmt(item["credits"], 1)])
        table = Table(table_data, colWidths=[20*mm, 63*mm, 16*mm, 16*mm, 16*mm, 16*mm, 15*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8), ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#e0dbd0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f3ee")]),
        ]))
        story.extend([table, Spacer(1, 8)])
    doc.build(story)
    output.seek(0)
    return output.getvalue()


@require_http_methods(["GET", "POST"])
def home(request):
    try:
        df, semester_metrics = dataset()
    except Exception:
        # Avoid exposing workbook paths or stack traces to visitors.
        return render(request, "results/home.html", {
            "error": "The academic workbook could not be loaded. Check the configured RESULTS_WORKBOOK file.",
            "page": "Home",
        }, status=503)

    page = request.POST.get("page", request.GET.get("page", "Home"))
    allowed_pages = {"Home", "Results", "My Analytics", "Comparison", "Goals"}
    if page not in allowed_pages:
        page = "Home"

    context = {"page": page, "error": "", "result": None, "analytics": None,
               "comparison": None, "goal": None, "all_pages": ["Results", "My Analytics", "Comparison", "Goals"]}

    if request.method == "POST":
        # Simple per-session submission throttle for lookup/comparison endpoints.
        now = int(time.time())
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        throttle_key = f"results-post:{session_key}"
        last = cache.get(throttle_key)
        if last and now - last < 1:
            context["error"] = "Please wait a moment before submitting again."
        else:
            cache.set(throttle_key, now, timeout=2)

    if page == "Results" and request.method == "POST" and not context["error"]:
        roll = "".join(request.POST.get("roll_number", "").split()).upper()
        if not roll or len(roll) > 30 or not roll.isalnum():
            context["error"] = "Enter a valid hall-ticket number."
        else:
            student = df[df["rollNumber"].astype(str).str.upper() == roll].copy()
            if student.empty:
                context["error"] = "No result was found for that hall-ticket number."
            else:
                summary = student_summary(student, semester_metrics)
                all_semesters = sorted(df["semester"].astype(str).unique(), key=semester_sort_key)
                summary["all_semesters"] = all_semesters
                summary["attempted_semesters"] = set(student["semester"].astype(str))
                summary.update(extended_academic_views(student))
                summary["subjects"] = [{
                    "semester": str(row["semester"]), "code": str(row["subjectCode"]),
                    "name": str(row["subjectName"]), "internal": fmt(row["internal"], 1),
                    "external": fmt(row["external"], 1), "total": fmt(row["total"], 1),
                    "grade": str(row["grade"]), "credits": fmt(row["credits"], 1)
                } for _, row in student.assign(_sem_sort=student["semester"].astype(str).map(semester_sort_key)).sort_values("_sem_sort").drop(columns="_sem_sort").iterrows()]
                context["result"] = summary
                request.session["last_roll"] = roll

    elif page == "My Analytics" and request.method == "POST" and not context["error"]:
        roll = "".join(request.POST.get("roll_number", "").split()).upper()
        student = df[df["rollNumber"].astype(str).str.upper() == roll].copy() if roll else pd.DataFrame()
        if student.empty:
            context["error"] = "Enter a valid hall-ticket number with available results."
        else:
            summary = student_summary(student, semester_metrics)
            summary.update(extended_academic_views(student))
            summary["subjects"] = [{
                "semester": str(row["semester"]), "subject": str(row["subjectName"]),
                "code": str(row["subjectCode"]), "total": fmt(row["total"], 1),
                "grade": str(row["grade"]), "internal": fmt(row["internal"], 1),
                "external": fmt(row["external"], 1)
            } for _, row in student.iterrows()]
            context["analytics"] = summary
            request.session["last_roll"] = roll

    elif page == "Comparison" and request.method == "POST" and not context["error"]:
        roll_a = "".join(request.POST.get("roll_a", "").split()).upper()
        roll_b = "".join(request.POST.get("roll_b", "").split()).upper()
        a = df[df["rollNumber"].astype(str).str.upper() == roll_a].copy()
        b = df[df["rollNumber"].astype(str).str.upper() == roll_b].copy()
        if a.empty or b.empty:
            context["error"] = "Enter two valid hall-ticket numbers with available results."
        elif roll_a == roll_b:
            context["error"] = "Choose two different students to compare."
        else:
            sa, sb = student_summary(a, semester_metrics), student_summary(b, semester_metrics)
            xa, xb = extended_academic_views(a), extended_academic_views(b)
            comparison_rows = []
            for label, key in [("CGPA", "cgpa_display"), ("Average marks", "avg_display"),
                               ("Pass percentage", "pass_display"), ("Recorded credits", "credits_display")]:
                comparison_rows.append({"label": label, "a": sa[key], "b": sb[key]})
            merged = a[["semester","subjectCode","subjectName","total","grade"]].merge(
                b[["semester","subjectCode","subjectName","total","grade"]],
                on=["semester","subjectCode","subjectName"], how="inner", suffixes=("_a","_b"))
            subjects = [{
                "semester": str(row["semester"]), "subject": str(row["subjectName"]),
                "a": fmt(row["total_a"], 1), "b": fmt(row["total_b"], 1),
                "gap": fmt(safe_float(row["total_a"]) - safe_float(row["total_b"]), 1),
                "grade_a": str(row["grade_a"]), "grade_b": str(row["grade_b"])
            } for _, row in merged.iterrows()]
            semester_a = {row["semester"]: row for row in xa["semester_performance"]}
            semester_b = {row["semester"]: row for row in xb["semester_performance"]}
            semester_comparison = []
            for sem in sorted(set(semester_a) | set(semester_b), key=lambda x: tuple(int(p) if p.isdigit() else p for p in x.replace("_", "-").split("-"))):
                ra, rb = semester_a.get(sem, {}), semester_b.get(sem, {})
                semester_comparison.append({
                    "semester": sem, "avg_a": ra.get("average", "—"), "avg_b": rb.get("average", "—"),
                    "pass_a": ra.get("pass_rate", "—"), "pass_b": rb.get("pass_rate", "—"),
                    "backlogs_a": ra.get("backlogs", "—"), "backlogs_b": rb.get("backlogs", "—"),
                })
            type_comparison = []
            for ra, rb in zip(xa["theory_lab"], xb["theory_lab"]):
                type_comparison.append({"type": ra["type"], "internal_a": ra["internal"], "internal_b": rb["internal"],
                    "external_a": ra["external"], "external_b": rb["external"],
                    "total_a": ra["total"], "total_b": rb["total"]})
            grade_comparison = [{"grade": ra["grade"], "count_a": ra["count"], "count_b": rb["count"]}
                                for ra, rb in zip(xa["grade_counts"], xb["grade_counts"])]
            movement_a = {row["semester"]: row for row in sgpa_movement(a, semester_metrics)}
            movement_b = {row["semester"]: row for row in sgpa_movement(b, semester_metrics)}
            movement_rows = []
            for sem in sorted(set(movement_a) | set(movement_b), key=semester_sort_key):
                ma, mb = movement_a.get(sem, {}), movement_b.get(sem, {})
                movement_rows.append({"semester": sem, "sgpa_a": ma.get("sgpa", "—"),
                    "sgpa_b": mb.get("sgpa", "—"), "movement_a": ma.get("movement", "—"),
                    "movement_b": mb.get("movement", "—")})
            backlogs_a = [{"semester": str(row["semester"]), "code": str(row["subjectCode"]),
                "subject": str(row["subjectName"]), "grade": str(row["grade"])}
                for _, row in a[a["grade"].isin(["F", "AB"])].iterrows()]
            backlogs_b = [{"semester": str(row["semester"]), "code": str(row["subjectCode"]),
                "subject": str(row["subjectName"]), "grade": str(row["grade"])}
                for _, row in b[b["grade"].isin(["F", "AB"])].iterrows()]
            context["comparison"] = {"a": sa, "b": sb, "rows": comparison_rows, "subjects": subjects,
                "semester_rows": semester_comparison, "type_rows": type_comparison, "grade_rows": grade_comparison,
                "movement_rows": movement_rows, "backlogs_a": backlogs_a, "backlogs_b": backlogs_b,
                "roll_a": roll_a, "roll_b": roll_b}

    elif page == "Goals" and request.method == "POST" and not context["error"]:
        current = min(10.0, max(0.0, safe_float(request.POST.get("current_cgpa"))))
        completed = max(0.0, safe_float(request.POST.get("completed_credits")))
        remaining = max(0.0, safe_float(request.POST.get("remaining_credits")))
        target = min(10.0, max(0.0, safe_float(request.POST.get("target_cgpa"), 8.0)))
        if remaining <= 0:
            context["error"] = "Enter future credits greater than zero to run scenarios."
        else:
            scenarios = [{"future": f"{sgpa:.1f}",
                          "projected": fmt(project_cgpa(current, completed, remaining, sgpa), 3)}
                         for sgpa in [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]]
            required = what_if_cgpa(current, completed, remaining, target)
            context["goal"] = {"current": f"{current:.2f}", "completed": f"{completed:g}",
                "remaining": f"{remaining:g}", "target": f"{target:.2f}", "scenarios": scenarios,
                "required": fmt(required), "possible": required is not None and required <= 10,
                "already": current >= target}

    context["default_roll"] = request.session.get("last_roll", "")
    return render(request, "results/home.html", context)


@require_GET
def export_data(request, kind):
    if kind not in {"csv", "xlsx", "pdf", "compare-csv", "compare-xlsx"}:
        raise Http404
    try:
        df, semester_metrics = dataset()
    except Exception:
        return HttpResponse("Workbook unavailable.", status=503)
    if kind in {"compare-csv", "compare-xlsx"}:
        roll_a = "".join(request.GET.get("roll_a", "").split()).upper()
        roll_b = "".join(request.GET.get("roll_b", "").split()).upper()
        if (not roll_a or not roll_b or len(roll_a) > 30 or len(roll_b) > 30
                or not roll_a.isalnum() or not roll_b.isalnum() or roll_a == roll_b):
            return HttpResponse("Two different valid hall-ticket numbers are required.", status=400)
        a = df[df["rollNumber"].astype(str).str.upper() == roll_a].copy()
        b = df[df["rollNumber"].astype(str).str.upper() == roll_b].copy()
        if a.empty or b.empty:
            return HttpResponse("One or both student records were not found.", status=404)
        sa, sb = student_summary(a, semester_metrics), student_summary(b, semester_metrics)
        metric_rows = pd.DataFrame([
            {"Metric": "CGPA", roll_a: sa["cgpa"], roll_b: sb["cgpa"]},
            {"Metric": "Average Marks", roll_a: sa["avg_marks"], roll_b: sb["avg_marks"]},
            {"Metric": "Pass %", roll_a: sa["pass_rate"], roll_b: sb["pass_rate"]},
            {"Metric": "Recorded Credits", roll_a: sa["credits"], roll_b: sb["credits"]},
            {"Metric": "Backlog Records", roll_a: sa["backlogs"], roll_b: sb["backlogs"]},
        ])
        xa, xb = extended_academic_views(a), extended_academic_views(b)
        type_rows = pd.DataFrame(xa["theory_lab"]).merge(
            pd.DataFrame(xb["theory_lab"]), on="type", suffixes=(f"_{roll_a}", f"_{roll_b}"))
        grade_rows = pd.DataFrame(xa["grade_counts"]).merge(
            pd.DataFrame(xb["grade_counts"]), on="grade", suffixes=(f"_{roll_a}", f"_{roll_b}"))
        sem_a = pd.DataFrame(xa["semester_performance"]).rename(columns={
            "average": f"average_{roll_a}", "pass_rate": f"pass_rate_{roll_a}", "backlogs": f"backlogs_{roll_a}"})
        sem_b = pd.DataFrame(xb["semester_performance"]).rename(columns={
            "average": f"average_{roll_b}", "pass_rate": f"pass_rate_{roll_b}", "backlogs": f"backlogs_{roll_b}"})
        sem_rows = sem_a.merge(sem_b, on="semester", how="outer")
        common = a[["semester", "subjectCode", "subjectName", "total", "grade"]].merge(
            b[["semester", "subjectCode", "subjectName", "total", "grade"]],
            on=["semester", "subjectCode", "subjectName"], how="inner", suffixes=(f"_{roll_a}", f"_{roll_b}"))
        frames = {
            "Academic Performance": metric_rows,
            "Semester Performance": sem_rows,
            "Theory vs Lab": type_rows,
            "Grades & Backlogs": grade_rows,
            "Common Subjects": common,
        }
        filename = f"{roll_a}_vs_{roll_b}_comparison"
        if kind == "compare-csv":
            combined = []
            for section, frame in frames.items():
                piece = frame.copy()
                piece.insert(0, "Section", section)
                combined.append(piece)
            response = HttpResponse(pd.concat(combined, ignore_index=True, sort=False).to_csv(index=False),
                                    content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
            return response
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for sheet, frame in frames.items():
                frame.to_excel(writer, index=False, sheet_name=sheet[:31])
        response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
        return response

    roll = "".join(request.GET.get("roll", "").split()).upper()
    if not roll or len(roll) > 30 or not roll.isalnum():
        return HttpResponse("A valid hall-ticket number is required.", status=400)
    student = df[df["rollNumber"].astype(str).str.upper() == roll].copy()
    if student.empty:
        return HttpResponse("No results found.", status=404)
    if kind == "csv":
        response = HttpResponse(student.to_csv(index=False), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="results-{roll}.csv"'
        return response
    if kind == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            student.to_excel(writer, index=False, sheet_name="Results")
        response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="results-{roll}.xlsx"'
        return response
    summary = student_summary(student, semester_metrics)
    summary["all_semesters"] = sorted(df["semester"].astype(str).unique(), key=semester_sort_key)
    response = HttpResponse(make_pdf(summary, student, semester_metrics), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="results-{roll}.pdf"'
    return response
