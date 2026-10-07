# 🎓 Results App

**Results App** is an academic performance intelligence platform built with **Python, Pandas, OpenPyXL, Streamlit, Plotly, and ReportLab**.

It converts semester-wise Excel result data into a structured analytics workflow for student performance, batch analysis, subject difficulty, backlog analysis, what-if CGPA planning, reporting, and optional GenAI interpretation.

## 🌐 Live Demo

[Open the deployed Results App](https://academic-results.streamlit.app/)

## 🧠 Project Architecture

**Excel → Normalization → Validation → Deterministic Academic Metrics → Analytics → Visualization/Reporting → Optional GenAI Interpretation**

A key design decision is that **numerical calculations remain deterministic**. The GenAI layer receives calculated metrics and explains them in natural language; it does not calculate or alter marks, grades, SGPA, or CGPA.

## 📊 What This Project Demonstrates

- Excel data ingestion and transformation
- Pandas-based analytics
- Data validation and quality checks
- KPI and academic metric calculation
- Student-level performance analytics
- Batch-level analytics
- Subject difficulty analysis
- Backlog analysis
- What-if / scenario analysis
- Interactive visualization
- PDF reporting
- GenAI integration with grounded prompts
- Streamlit multipage application architecture

## ✨ Features

### 🎓 Student Performance Intelligence
- Semester-wise result lookup
- SGPA and credit-weighted CGPA
- Performance scorecard
- Average marks
- Credits
- Pass rate
- Backlog count
- Strong and weak subject identification
- SGPA trend
- Rule-based academic insights

### 📊 Batch Analytics
- Branch-wise average CGPA
- Batch average pass rate
- Students with backlogs
- Grade distribution
- Top performers
- Branch filtering

### 📚 Subject Difficulty Analysis
- Average marks
- Pass rate
- Failure rate
- Attempt count
- Highest-risk subjects

### 📌 Backlog Analytics
- Backlog record count
- Students affected by backlogs
- Subject-level backlog rate
- Semester-wise backlog concentration
- Students with highest backlog counts
- Detailed backlog records

### 🎯 What-if CGPA
- Required future SGPA for a target CGPA
- Projected final CGPA for a planned future SGPA
- Mathematical reachability check for targets

### ✨ GenAI Academic Analyst
The optional AI layer uses verified metrics such as:
- CGPA
- Average marks
- Pass rate
- Backlog count
- SGPA trend
- Strong subjects
- Weak subjects
- Deterministic insights

The model is explicitly instructed not to invent academic facts or institutional policies.

Configure GEMINI_API_KEY through Streamlit Secrets/environment variables, or enter a key temporarily in the AI page.

### 🛡️ Data Quality
Validation checks include:
- Missing roll numbers
- Missing names/subjects
- Missing grades
- Invalid grade codes
- Invalid credits
- Marks outside the expected range
- Duplicate subject records

## 🧮 Analytics Logic

### SGPA

**SGPA = Σ(Grade Point × Credits) / Σ(Credits)**

### CGPA

**CGPA = Σ(Semester SGPA × Semester Credits) / Σ(Total Semester Credits)**

The workbook's semester-level SGPA/credit values are preferred when available.

## 📁 Project Structure

    Results/
    ├── ui.py
    ├── academic_analytics.py
    ├── genai_insights.py
    ├── pages/
    │   ├── Academic Intelligence.py
    │   └── Backlog Analytics.py
    ├── results.xlsx
    ├── requirements.txt
    ├── README.md
    └── images/

The original Results UI remains in ui.py. The new analytics capabilities are implemented as Streamlit multipage modules, reducing risk to the existing application while making the project easier to extend.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python** | Application logic and analytics |
| **Pandas** | Data processing and transformation |
| **OpenPyXL** | Excel workbook parsing |
| **Streamlit** | Interactive multipage application |
| **Plotly** | Interactive charts |
| **ReportLab** | PDF reporting |
| **Gemini API** | Optional GenAI interpretation |

## 🚀 Run Locally

    git clone https://github.com/PrahitViraajReddy/Results.git
    cd Results
    pip install -r requirements.txt
    streamlit run ui.py

Streamlit will expose the existing application plus the new Academic Intelligence and Backlog Analytics pages.

## 🔐 Data Privacy

The application processes student-level academic records. Public deployments should use synthetic, anonymized, or appropriately authorized data.

Do not publish real student records publicly without authorization.

## 🔮 Future Improvements

- SQLite/PostgreSQL backend
- Excel/CSV → ETL pipeline
- Authentication and role-based access
- Admin dashboard
- Automated scheduled data ingestion
- Versioned data-quality reports
- More advanced cohort analytics

## 👤 Author

**Prahit Viraaj Reddy**

- GitHub: [@PrahitViraajReddy](https://github.com/PrahitViraajReddy)
- Live App: [academic-results.streamlit.app](https://academic-results.streamlit.app/)

## ⚠️ Disclaimer

This project is an educational and portfolio project. Analytics depend on the quality and completeness of the supplied academic data.
