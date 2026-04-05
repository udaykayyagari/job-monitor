#!/usr/bin/env python3
"""
AI-Powered Job Scraper & Monitor
Searches for jobs, scrapes them, scores with AI, and sends notifications.
Optimized for GitHub Actions free tier.
"""

import os
import json
import smtplib
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# ========== CONFIGURATION ==========
# Target job titles (add as many as you want)
TARGET_TITLES = [
    "Digital Transformation Lead",
    "AI Automation Lead",
    "Intelligent Automation Lead",
    "Head of AI",
    "AI Practice Lead",
    "GenAI Lead",
    "Director of Automation",
    "VP of Digital Transformation"
]

# Keywords for scoring (weighted)
KEYWORDS = {
    "AI Agent": 3,
    "Agentic AI": 3,
    "Digital Transformation": 3,
    "Intelligent Automation": 3,
    "Finance Transformation": 2,
    "RPA": 2,
    "GenAI": 3,
    "LLM": 2,
    "Hyperautomation": 2,
    "Travel and Expense": 1,
    "Cash Application": 2,
    "Invoice Processing": 2,
    "Reconciliations": 1,
    "Procurement Audit": 2,
    "Laytime": 2,
    "Settlement Process": 2,
    "Global Trade Execution": 3,
    "Data Visualisation": 1
}

# Email configuration (will be loaded from GitHub Secrets)
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# AI configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ========== JOB SEARCH FUNCTIONS ==========

def search_linkedin_jobs() -> List[Dict]:
    """Scrape LinkedIn jobs using a simplified approach."""
    # Note: For production, use a more robust method or API
    # This is a simplified example using RSS feeds where available
    jobs = []
    
    # Example: Indeed RSS feed (replace with actual search URL)
    for title in TARGET_TITLES:
        search_url = f"https://rss.indeed.com/rss?q={title.replace(' ', '+')}&l="
        try:
            response = requests.get(search_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'xml')
            for item in soup.find_all('item'):
                jobs.append({
                    'title': item.title.text if item.title else title,
                    'company': item.find('source').text if item.find('source') else 'Unknown',
                    'link': item.link.text if item.link else '',
                    'description': item.description.text if item.description else '',
                    'source': 'Indeed'
                })
        except Exception as e:
            print(f"Error searching {title}: {e}")
    
    return jobs

def score_job_with_ai(job: Dict, resume_text: str = "") -> Dict:
    """Use AI to score job against resume and keywords."""
    # Keyword-based scoring (fast, no API cost)
    description = (job.get('title', '') + " " + job.get('description', '')).lower()
    keyword_score = 0
    matched_keywords = []
    
    for kw, weight in KEYWORDS.items():
        if kw.lower() in description:
            keyword_score += weight
            matched_keywords.append(kw)
    
    # AI scoring (more accurate, uses API)
    ai_score = 0
    ai_reason = ""
    
    if GEMINI_API_KEY and resume_text:
        try:
            prompt = f"""
            Score this job from 0-100 for a Digital Transformation Lead with expertise in Agentic AI, 
            Finance Automation, and Global Trade Execution. Consider keyword matches and overall fit.
            
            Resume: {resume_text[:500]}
            
            Job Title: {job.get('title')}
            Company: {job.get('company')}
            Description: {job.get('description', '')[:1000]}
            
            Return only: SCORE: [number] | REASON: [brief reason]
            """
            response = model.generate_content(prompt)
            result = response.text
            
            # Parse AI response
            score_match = re.search(r'SCORE:\s*(\d+)', result)
            if score_match:
                ai_score = int(score_match.group(1))
            
            reason_match = re.search(r'REASON:\s*(.+)', result)
            if reason_match:
                ai_reason = reason_match.group(1)
                
        except Exception as e:
            print(f"AI scoring failed: {e}")
    
    # Combine scores (70% AI, 30% keyword)
    if ai_score > 0:
        final_score = (ai_score * 0.7) + ((keyword_score / sum(KEYWORDS.values())) * 100 * 0.3)
    else:
        final_score = (keyword_score / sum(KEYWORDS.values())) * 100
    
    return {
        'score': round(final_score, 1),
        'keyword_score': keyword_score,
        'ai_score': ai_score,
        'matched_keywords': matched_keywords,
        'ai_reason': ai_reason
    }

def generate_interview_guide(job: Dict, score_data: Dict) -> str:
    """Create a custom interview guide based on the job and match score."""
    guide = f"""
    <h2>🎯 Job Match Alert: {job.get('title')} at {job.get('company')}</h2>
    <p><strong>Match Score:</strong> {score_data['score']}/100</p>
    <p><strong>Job Link:</strong> <a href="{job.get('link')}">Click to Apply</a></p>
    <p><strong>Matched Keywords:</strong> {', '.join(score_data['matched_keywords'][:5])}</p>
    
    <h3>📋 Custom Interview Guide for This Role</h3>
    
    <h4>1. Company Research (30 min):</h4>
    <ul>
        <li>Read {job.get('company')}'s latest annual report & press releases</li>
        <li>Research their digital transformation maturity</li>
        <li>Find the hiring manager on LinkedIn</li>
    </ul>
    
    <h4>2. Tailor Your 3 Key Stories:</h4>
    <ul>
        <li><strong>Revenue Recovery:</strong> "I recovered $3M using Agentic AI for invoice collection"</li>
        <li><strong>Tariff Agility:</strong> "Updated 7,000 man-hours of contracts in 72 hours during a trade crisis"</li>
        <li><strong>Process Efficiency:</strong> "Reduced 500 monthly verifications to 30 – 94% touchless"</li>
    </ul>
    
    <h4>3. Questions to Ask Them:</h4>
    <ul>
        <li>What is the single biggest operational bottleneck in your finance function?</li>
        <li>How do you measure success for AI/automation initiatives?</li>
        <li>What would "winning" look like in the first 90 days?</li>
    </ul>
    
    <h4>4. Technical Prep:</h4>
    <ul>
        <li>Be ready to explain Agentic AI vs RPA</li>
        <li>Know how to calculate ROI (manual cost + error cost vs development cost)</li>
        <li>Have a 2-minute demo of a past automation (use the tariff story)</li>
    </ul>
    
    <hr>
    <p><em>Generated automatically by your AI Job Monitor</em></p>
    """
    return guide

def send_email_notification(job: Dict, score_data: Dict):
    """Send email with custom interview guide."""
    if not all([EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD]):
        print("Email credentials not configured. Skipping notification.")
        return
    
    subject = f"🔥 {score_data['score']}/100 Match: {job.get('title')} at {job.get('company')}"
    body = generate_interview_guide(job, score_data)
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent for {job.get('title')} at {job.get('company')}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def save_job_history(job: Dict, score_data: Dict):
    """Save job to history file to avoid duplicate notifications."""
    history_file = "job_history.json"
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    # Check if already exists
    job_id = f"{job.get('title')}|{job.get('company')}|{job.get('link')}"
    if any(j.get('id') == job_id for j in history):
        return False
    
    history.append({
        'id': job_id,
        'title': job.get('title'),
        'company': job.get('company'),
        'link': job.get('link'),
        'score': score_data['score'],
        'notified_at': datetime.now().isoformat()
    })
    
    # Keep only last 500 entries
    history = history[-500:]
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    return True

def main():
    """Main execution function."""
    print(f"Starting job scan at {datetime.now()}")
    
    # Search for jobs
    print("Searching for jobs...")
    jobs = search_linkedin_jobs()
    print(f"Found {len(jobs)} jobs")
    
    # Score and filter
    matches_found = 0
    for job in jobs:
        score_data = score_job_with_ai(job)
        
        # Only notify for high-quality matches (score >= 50)
        if score_data['score'] >= 50:
            if save_job_history(job, score_data):
                print(f"Match found! Score: {score_data['score']} - {job.get('title')}")
                send_email_notification(job, score_data)
                matches_found += 1
    
    print(f"Scan complete. Found {matches_found} new matches.")
    
    # Optional: Send a summary email
    if matches_found == 0:
        print("No new matches today.")

if __name__ == "__main__":
    main()