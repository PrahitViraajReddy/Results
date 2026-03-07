import requests
import csv
import time

API_URL = "https://jntuhresults.dhethi.com/api/getAcademicResult"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://jntuhconnect.dhethi.com",
    "referer": "https://jntuhconnect.dhethi.com/",
    "user-agent": "Mozilla/5.0"
}

# -------- Load hall tickets --------
try:
    with open("halltickets.txt", "r") as f:
        hall_tickets = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("halltickets.txt not found")
    exit()

rows = []

print(f"Fetching results for {len(hall_tickets)} students...\n")

for htno in hall_tickets:
    try:
        params = {"rollNumber": htno.upper()}
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"❌ {htno} -> Status {response.status_code}")
            continue

        data = response.json()

        if not data:
            print(f"⚠️ No data for {htno}")
            continue

        details = data.get("details", {})
        semesters = data.get("results", {}).get("semesters", [])

        name = details.get("name", "")
        branch = details.get("branch", "")

        for sem in semesters:
            semester = sem.get("semester")

            for sub in sem.get("subjects", []):
                rows.append({
                    "rollNumber": htno,
                    "name": name,
                    "branch": branch,
                    "semester": semester,
                    "subjectCode": sub.get("subjectCode"),
                    "subjectName": sub.get("subjectName"),
                    "internal": sub.get("internalMarks"),
                    "external": sub.get("externalMarks"),
                    "total": sub.get("totalMarks"),
                    "grade": sub.get("grades"),
                    "credits": sub.get("credits")
                })

        print(f"✅ {htno}")

        time.sleep(0.1)

    except Exception as e:
        print(f"⚠️ Error {htno}: {e}")


# -------- Save CSV --------

if rows:
    keys = rows[0].keys()

    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} subject records to results.csv")

else:
    print("No results collected.")
