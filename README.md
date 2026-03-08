# 🎓 Results App — Academic Results Portal

A clean and modern Streamlit web app to view, analyze, and compare student academic results.

---

## ✨ Features

- **📋 Results** — Enter Hall Ticket Number to view semester-wise results with SGPA and CGPA
- **💡 Insights** — Subject performance chart, SGPA progression, best & weak subjects
- **⚖️ Comparison** — Compare two students side by side with winner card, subject analysis, and improvement trends

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/PrahitViraajReddy/Results.git
cd Results
```


### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your data
Place your `results.csv` file in the project folder.

### 4. Run the app
```bash
streamlit run ui.py
```

---

## 📁 Project Structure

```
Results/
├── ui.py                  # Main Streamlit app
├── results.csv            # Student results data
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## 📊 CSV Format

Your `results.csv` should have these columns:

| Column | Description |
|--------|-------------|
| `rollNumber` | Student Hall Ticket Number |
| `name` | Student Name |
| `branch` | Branch / Department |
| `semester` | Semester (e.g. 1-1, 1-2) |
| `subjectCode` | Subject Code |
| `subjectName` | Subject Name |
| `internal` | Internal Marks |
| `external` | External Marks |
| `total` | Total Marks |
| `grade` | Grade (O, A+, A, B+, B, C, F) |
| `credits` | Subject Credits |

---

## 🧮 SGPA & CGPA Formula

**SGPA** = Σ(Grade Point × Credits) ÷ Σ(Credits) — per semester

**CGPA** = Σ(Semester SGPA × Semester Credits) ÷ Σ(Total Credits) — all semesters

> SGPA is only calculated if the student has passed all subjects in that semester (no F or Ab grades).
> CGPA is only calculated if all semesters are passed.

---

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) — Web framework
- [Pandas](https://pandas.pydata.org/) — Data processing
- [Plotly](https://plotly.com/) — Interactive charts

---

## 📬 Contact

Made by **Prahit Viraaj Reddy**  
GitHub: [@PrahitViraajReddy](https://github.com/PrahitViraajReddy)