# job_search_automation/notification_manager.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from db_manager import job_data_to_dict  # For converting tuples to dicts if needed

load_dotenv()  # Load environment variables

EMAIL_SENDER = os.environ.get("JOB_SEARCH_EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("JOB_SEARCH_EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("JOB_SEARCH_EMAIL_RECIPIENT")
SMTP_SERVER = os.environ.get("JOB_SEARCH_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("JOB_SEARCH_SMTP_PORT", 465))


def send_email_notification(new_jobs_raw):
    """Sends an email with a summary of new job listings."""
    if not new_jobs_raw:
        print("No new jobs to report via email.")
        return

    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        print(
            "Email credentials or recipient not fully configured in .env. Skipping email notification."
        )
        return

    new_jobs = [job_data_to_dict(job) for job in new_jobs_raw]

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg["Subject"] = f"New Job Listings Found! ({len(new_jobs)} jobs)"

    body = "Hello,\n\nHere are the new job listings that match your criteria, ordered by date posted:\n\n"
    for job in new_jobs:
        body += f"Title: {job['title']}\n"
        body += f"Company: {job['company']}\n"
        body += f"Location: {job['location']}\n"
        body += f"URL: {job['url']}\n"
        body += f"Date Posted: {job['date_posted']} (Found: {job['date_found']})\n"
        body += f"Relevance Score: {job['relevance_score']}\n"
        body += "-" * 60 + "\n\n"

    body += "Happy job hunting!\nYour Automated Job Search Script"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(
            f"Email notification sent successfully to {EMAIL_RECIPIENT} with {len(new_jobs)} new jobs!"
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(
            "Please check your email sender, password, SMTP server, and port settings."
        )
        print("For Gmail, you might need to use an 'App password' if 2FA is enabled.")
