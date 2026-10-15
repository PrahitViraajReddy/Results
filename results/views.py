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
    GRADE_POINTS, PASS_GRADES, load_academic_data, student_metrics,
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
    for semester in sorted(rows["semester"].astype(str).unique(), key=lambda s: [int(x) if x.isdigit() else x for x in s.replace("_","-").split("-")]):
        story.append(Paragraph(f"Semester {semester}", styles["Heading2"]))
        sem = rows[rows["semester"].astype(str) == semester]
        table_data = [["Code", "Subject", "Internal", "External", "Total", "Grade", "Credits"]]
        for _, item in sem.iterrows():
            table_data.append([str(item["subjectCode"]), str(item["subjectName"]),
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
                all_semesters = sorted(df["semester"].astype(str).unique())
                summary["all_semesters"] = all_semesters
                summary["subjects"] = [{
                    "semester": str(row["semester"]), "code": str(row["subjectCode"]),
                    "name": str(row["subjectName"]), "internal": fmt(row["internal"], 1),
                    "external": fmt(row["external"], 1), "total": fmt(row["total"], 1),
                    "grade": str(row["grade"]), "credits": fmt(row["credits"], 1)
                } for _, row in student.sort_values("semester").iterrows()]
                context["result"] = summary
                request.session["last_roll"] = roll

    elif page == "My Analytics" and request.method == "POST" and not context["error"]:
        roll = "".join(request.POST.get("roll_number", "").split()).upper()
        student = df[df["rollNumber"].astype(str).str.upper() == roll].copy() if roll else pd.DataFrame()
        if student.empty:
            context["error"] = "Enter a valid hall-ticket number with available results."
        else:
            summary = student_summary(student, semester_metrics)
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
            context["comparison"] = {"a": sa, "b": sb, "rows": comparison_rows, "subjects": subjects}

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
    if kind not in {"csv", "xlsx", "pdf"}:
        raise Http404
    try:
        df, semester_metrics = dataset()
    except Exception:
        return HttpResponse("Workbook unavailable.", status=503)
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
    response = HttpResponse(make_pdf(summary, student, semester_metrics), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="results-{roll}.pdf"'
    return response
