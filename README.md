# 🎓 Results App

**Results App** is a student-focused academic performance platform built with **Python, Pandas, OpenPyXL, Streamlit, Plotly, and ReportLab**.

It converts semester-wise Excel result data into a structured workflow for **result lookup, personal academic analytics, student-to-student comparison, what-if CGPA planning, visualization, and reporting**.

## 🌐 Live Demo

[Open the deployed Results App](https://academic-results.streamlit.app/)

## 🎯 Project Focus

This is a **student platform**, not a college/admin analytics dashboard.

The application is designed around a simple distinction:
- **Results** → What did I score?
- **My Analytics** → How am I performing, where am I improving/declining, and what should I investigate?
- **Comparison** → How do two students differ across comparable academic metrics?
- **Goals** → What future SGPA would be needed to reach a target CGPA?

All academic calculations are deterministic and derived from the supplied workbook.

## ✨ Features

### 📋 Results
- Hall-ticket based result lookup
- Semester-wise subject results
- Internal, external and total marks
- Grade and credit information
- SGPA/CGPA display
- Academic performance summary
- PDF result/report export

### 📊 My Analytics
- CGPA
- Average marks
- Grade-point average
- Pass percentage
- Recorded and passed credits
- SGPA volatility and range
- Best and weakest semester
- Semester-to-semester movement
- Strongest subjects
- Subjects needing attention
- Semester performance breakdown
- Subject-level marks analysis
- Theory vs Lab internal/external averages
- Grade and backlog summary
- What-if CGPA scenarios
- Target CGPA planning
- Internal vs external performance analysis

**Important:** missing semesters are not treated as zero. Semester movement is calculated only when the recorded semesters are actually consecutive.

### ⚖️ Comparison
- CGPA
- Average marks
- Pass percentage
- Recorded credits
- F/AB backlog records
- Semester SGPA
- Semester movement
- Semester performance
- Theory vs Lab performance
- Common-subject marks and grades
- Subject-wise marks gaps
- Grade/backlog comparison

If a student has no recorded result for a semester, that missing semester is preserved as missing rather than being converted into a zero.

### 🎯 Goal & What-if Analysis
- Enter future credits to model
- Test future SGPA scenarios
- Project final CGPA
- Set a target CGPA
- Calculate the required average future SGPA
- Identify targets that are mathematically unreachable under a 10-point SGPA scale

The application does **not** assume a remaining-credit total when the workbook does not provide one.

### 📤 Export
- CSV analytics export
- Excel analytics/comparison exports
- Existing result-report/PDF workflow

## 🧮 Academic Analytics Logic

### SGPA
**SGPA = Σ(Grade Point × Credits) / Σ(Credits)**

### CGPA
**CGPA = Σ(Semester SGPA × Semester Credits) / Σ(Total Semester Credits)**

Workbook-provided semester SGPA and credit values are preferred where available.

### Grade Handling
The application uses recorded grade information and distinguishes passing grades from **F/AB** records for backlog analysis.

### Missing Semester Handling
A missing result is **not** interpreted as a zero.

For semester movement:
- `1-1 → 1-2` is consecutive
- `1-2 → 2-1` is consecutive
- `3-1 → 4-1` is **not** consecutive if `3-2` is missing

This prevents misleading improvement/drop calculations.

## 🗂️ Application Structure

The main application remains in `ui.py`.

Supporting academic analytics logic is kept in:
- `academic_analytics.py`
- `results.xlsx`
- `requirements.txt`

The application uses the existing Streamlit UI rather than separate analytics pages, keeping the original Results experience intact while extending it with student-focused analytics and comparison workflows.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python** | Application logic and academic calculations |
| **Pandas** | Data processing and transformation |
| **OpenPyXL** | Excel workbook handling |
| **Streamlit** | Interactive web application |
| **Plotly** | Interactive visualizations |
| **ReportLab** | PDF report generation |

## 🚀 Run Locally

```bash
git clone https://github.com/PrahitViraajReddy/Results.git
cd Results
pip install -r requirements.txt
streamlit run ui.py
```

## 📁 Project Structure

```text
Results/
├── ui.py
├── academic_analytics.py
├── results.xlsx
├── requirements.txt
└── README.md
```

## 🔐 Data Privacy

The application processes student-level academic records.

If deploying publicly, use synthetic, anonymized, or appropriately authorized academic data. Do not publish real student records without authorization.

## 👤 Author

**Prahit Viraaj Reddy**

- GitHub: [@PrahitViraajReddy](https://github.com/PrahitViraajReddy)
- Live App: [academic-results.streamlit.app](https://academic-results.streamlit.app/)

## ⚠️ Disclaimer

This is an educational and portfolio project. Analytics depend on the quality, completeness, and structure of the supplied academic workbook.