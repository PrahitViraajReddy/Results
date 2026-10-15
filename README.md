# 🎓 Results App — Django migration

A student-facing academic results portal migrated from Streamlit to Django while retaining the existing visual direction: dark navy sidebar, warm ivory background, gold accents, DM Sans / DM Serif typography, responsive cards, and chart-based analytics.

## Current migration status

This branch replaces the Streamlit runtime with Django views and templates. It preserves the main workflows:
- Hall-ticket result lookup
- Semester/subject marks, grades, credits, SGPA/CGPA summary
- Personal analytics, performance insights, SGPA trend and subject summaries
- Two-student comparison
- CGPA what-if scenarios and future-SGPA projections
- PDF, CSV and Excel export for an individual student's results

The migration is an in-progress port. Validate parity against the original app and workbook before deploying or merging; do not assume pixel-perfect or feature-perfect parity until the test checklist below passes.

## Stack

- Django 5.2
- Pandas and OpenPyXL for workbook parsing
- Plotly.js for charts
- ReportLab for PDF reports
- Gunicorn for production WSGI serving

## Run locally

Use Python 3.11–3.13 for the smoothest compatibility with the pinned Django range.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Set the path to a workbook that you are authorized to use. Keep the workbook outside the public repository if it contains real student records.

**PowerShell**
```powershell
$env:RESULTS_WORKBOOK="C:\private-data\results.xlsx"
$env:DJANGO_SECRET_KEY="replace-with-a-long-random-secret"
$env:DJANGO_DEBUG="True"
python manage.py migrate
python manage.py check
python manage.py runserver
```

**macOS/Linux**
```bash
export RESULTS_WORKBOOK="/private-data/results.xlsx"
export DJANGO_SECRET_KEY="replace-with-a-long-random-secret"
export DJANGO_DEBUG="True"
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

The workbook is expected to contain a `Summary` sheet with `RollNumber`, `Name`, and `Branch`, plus semester sheets following the current workbook layout.

## Deployment configuration

Set these environment variables in your hosting provider:
- `DJANGO_SECRET_KEY`: a long, random secret; never commit it.
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames.
- `RESULTS_WORKBOOK`: absolute path to a private workbook mounted/provisioned at deploy time.
- `DJANGO_SECURE_SSL_REDIRECT=True` when HTTPS is configured.

Run `python manage.py migrate` as a release step and `python manage.py check --deploy` before production deployment and configure HTTPS at the host/proxy. Do not make the workbook publicly downloadable. Do not assume the existing Streamlit deployment will run Django; deploy this branch to a Django-capable host separately.

## Security notes

Django provides CSRF middleware, secure session-cookie settings in production mode, host validation, and escaped template output by default. This does **not** by itself guarantee that the application is secure. The current public hall-ticket lookup model still allows someone who knows a valid number to view that student's data. If results must be private to each student, add authenticated accounts and enforce per-student authorization before production.

The in-process/session throttle is only a lightweight guard, not a substitute for a shared production rate limiter. Configure rate limiting at the reverse proxy or use a shared cache/backend for multiple workers.

If a real `results.xlsx` was ever committed to a public repository, deleting it from the current branch does not erase prior Git history, forks, or existing copies. Rotate/restrict access as appropriate and consider history cleanup only with a deliberate repository-wide plan.

## Validation checklist

Before replacing the current live app:
1. Run `python manage.py check`.
2. Test valid and invalid hall-ticket lookups.
3. Compare every semester's subjects, marks, grade, credits and workbook SGPA against the existing app.
4. Check that missing semesters display **Not Applied for Exams**, not zero.
5. Verify CGPA/backlog rules and goal calculations against known examples.
6. Compare two students across semester movement, common subjects, grades/backlogs and theory/lab performance.
7. Open each PDF/CSV/Excel export and compare contents.
8. Test mobile layout, CSRF behavior, rate limiting, production settings and workbook privacy.

## Project structure

- `manage.py` — Django command entry point
- `results_site/` — settings, URL configuration, WSGI/ASGI
- `results/` — request handlers and Django templates
- `academic_analytics.py` — existing workbook parsing and deterministic academic calculations
- `results.xlsx` — **should be supplied privately at runtime**, not published with real student data
