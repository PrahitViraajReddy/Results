import os
import json
import urllib.request
import urllib.error


def build_ai_prompt(metrics, deterministic_insights):
    sgpa = ", ".join(f"Sem {sem}: {value:.2f}" for sem, value, _ in metrics["sgpa_rows"])
    best = ", ".join(f"{name}: {score:.1f}" for name, score in metrics["best_subjects"].items())
    weak = ", ".join(f"{name}: {score:.1f}" for name, score in metrics["weak_subjects"].items())

    return f"""You are an academic performance analyst.
Analyze ONLY the supplied verified metrics. Do not invent marks, subjects, semesters, causes, or institutional policies.
Return:
1. Performance summary
2. Two strengths
3. Two improvement priorities
4. One practical next-step plan
Keep it concise and student-friendly.

Student: {metrics["name"]}
Branch: {metrics["branch"]}
Calculated CGPA: {metrics["cgpa"] if metrics["cgpa"] is not None else "N/A"}
Average marks: {metrics["avg_marks"]:.1f}
Pass rate: {metrics["pass_rate"]:.1f}%
Backlog records: {metrics["backlogs"]}
SGPA trend: {sgpa or "N/A"}
Strong subjects: {best or "N/A"}
Weak subjects: {weak or "N/A"}

Deterministic insights:
{chr(10).join("- " + x for x in deterministic_insights)}
"""


def generate_gemini_insight(prompt, api_key=None, model="gemini-2.5-flash"):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return None, "GEMINI_API_KEY is not configured."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        return text, None
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        return None, f"AI service unavailable: {exc}"
