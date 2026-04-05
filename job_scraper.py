#!/usr/bin/env python3
"""
AI-Powered Job Monitor using Adzuna API (free, 100 requests/day)
Searches for Digital Transformation / AI Lead roles, scores them, and sends email alerts.
"""

import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ========== CONFIGURATION ==========
TARGET_TITLES = [
    "Digital Transformation Lead",
    "AI Automation Lead",
    "Intelligent Automation Lead",
    "Head of AI",
    "AI Practice Lead",
    "GenAI Lead",
    "Director of Digital Transformation"
]

KEYWORDS = {
    "AI Agent": 3, "Agentic AI": 3, "Digital Transformation": 3,
    "Intelligent Automation": 3, "Finance Transformation": 2,
    "RPA": 2, "GenAI": 3, "LLM": 2, "Hyperautomation": 2,
    "Travel and Expense": 1, "Cash Application": 2,
    "Invoice Processing": 2, "Reconciliations": 1,
    "Procurement Audit": 2, "Laytime": 2, "Settlement Process": 2,
    "Global Trade Execution": 3, "Data Visualisation": 1
}

# Email settings (from GitHub Secrets)
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# Adzuna API (free)
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY")
ADZUNA_COUNTRY = "in"   # Change to "in", "gb", "ca", etc. if needed

# ========== FUNCTIONS ==========
def search_adzuna():
    """Fetch jobs from Adzuna API for each target title."""
    jobs = []
    for title in TARGET_TITLES:
        url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_API_KEY,
            "what": title,
            "results_per_page": 10,
            "content-type": "application/json"
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            data = resp.json()
            for result in data.get("results", []):
                jobs.append({
                    "title": result.get("title", title),
                    "company": result.get("company", {}).get("display_name", "Unknown"),
                    "link": result.get("redirect_url", ""),
                    "description": result.get("description", ""),
                    "source": "Adzuna"
                })
        except Exception as e:
            print(f"Adzuna error for '{title}': {e}")
    return jobs

def score_job(job):
    """Score job based on keyword matches (0-100)."""
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    score = 0
    matched = []
    for kw, weight in KEYWORDS.items():
        if kw.lower() in text:
            score += weight
            matched.append(kw)
    max_possible = sum(KEYWORDS.values())
    normalized = (score / max_possible) * 100
    return round(normalized, 1), matched

def send_alert(job, score, matched):
    """Send email with job details and custom interview guide."""
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        print("Email credentials missing – cannot send alert.")
        return

    subject = f"🔥 {score}/100 Match: {job['title']} at {job['company']}"
    body = f"""
    <html>
    <body>
    <h2>🎯 Job Match Found</h2>
    <p><strong>Role:</strong> {job['title']}<br>
    <strong>Company:</strong> {job['company']}<br>
    <strong>Match Score:</strong> {score}/100<br>
    <strong>Keywords matched:</strong> {', '.join(matched[:5])}<br>
    <strong>Link:</strong> <a href="{job['link']}">Apply here</a></p>
    <hr>
    <h3>📋 Custom Interview Guide</h3>
    <ul>
        <li>Research {job['company']}'s digital transformation journey and recent news.</li>
        <li>Prepare your $3M revenue recovery story (AI agent for invoice collection).</li>
        <li>Practice explaining <strong>Agentic AI vs RPA</strong> and when to use each.</li>
        <li>Be ready to calculate ROI: manual cost + error cost vs development cost.</li>
        <li>Ask them: "What is the biggest bottleneck in your finance operations today?"</li>
    </ul>
    <p>Good luck! — Your AI Job Monitor</p>
    </body>
    </html>
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Alert sent for {job['title']} at {job['company']}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def save_history(job, score):
    """Prevent duplicate alerts for the same job."""
    history_file = "job_history.json"
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except:
        history = []
    job_id = f"{job['title']}|{job['company']}|{job['link']}"
    if any(h.get("id") == job_id for h in history):
        return False
    history.append({
        "id": job_id,
        "title": job["title"],
        "company": job["company"],
        "score": score,
        "notified_at": datetime.now().isoformat()
    })
    with open(history_file, "w") as f:
        json.dump(history[-500:], f, indent=2)
    return True

def main():
    print(f"🔍 Scanning jobs via Adzuna at {datetime.now()}")
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        print("❌ Adzuna API keys missing. Add ADZUNA_APP_ID and ADZUNA_API_KEY secrets.")
        return
    jobs = search_adzuna()
    print(f"📊 Found {len(jobs)} jobs")
    new_matches = 0
    for job in jobs:
        score, matched = score_job(job)
        if score >= 0:   # threshold for alert
            if save_history(job, score):
                send_alert(job, score, matched)
                new_matches += 1
    print(f"✅ Sent {new_matches} new job alerts")

if __name__ == "__main__":
    main()
