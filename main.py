# job_search_automation/main.py

import datetime
import os  # Import os for environment variables
import time

from dotenv import load_dotenv

# Import modules
from config import MIN_SKILL_MATCHES, RESUME_PATH, SCRAPING_DELAY_SECONDS
from db_manager import get_all_job_urls, save_job_listing, setup_database
from job_scraper import (
    scrape_all_jobs,
)
from resume_parser import create_search_query, parse_resume_keywords
from selenium_scraper import (
    get_selenium_driver,
)

# Load environment variables from .env file
load_dotenv()

# Email configuration from environment variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv(
    "SENDER_PASSWORD"
)  # IMPORTANT: Use app-specific passwords or secure methods
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")  # Can be the same as SENDER_EMAIL
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


def send_email_notification(job_details):
    """Sends an email notification for a new job posting."""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print(
            "Email credentials or receiver email not configured. Skipping email notification."
        )
        return

    import smtplib
    from email.mime.text import MIMEText

    subject = f"New Job Alert: {job_details['title']} at {job_details['company']}"
    body = f"""
    Hello,

    A new job matching your criteria has been found!

    Job Title: {job_details["title"]}
    Company: {job_details["company"]}
    Location: {job_details["location"]}
    Link: {job_details["url"]}

    Good luck with your application!

    Best regards,
    Your Job Search Script
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Email notification sent for: {job_details['title']}")
    except Exception as e:
        print(f"Error sending email: {e}")


def filter_and_process_job(job_data, resume_keywords):
    """
    Filters a single job listing based on keywords and preferences.
    Assumes job_data['description'] is already fetched.
    """
    title = job_data.get("title", "").lower()
    company = job_data.get("company", "").lower()
    location = job_data.get("location", "").lower()
    description = job_data.get("description", "").lower()
    url = job_data.get("url")

    # --- Filtering Logic ---
    is_remote = (
        "remote" in location
        or "work from home" in title
        or "worldwide" in location
        or "home office" in location
    )

    # Heuristic for international company / NGO
    is_international_company = (
        any(
            keyword in company
            for keyword in ["global", "international", "inc.", "corp."]
        )
        or "global" in description
        or "international" in description
        or "worldwide" in description
    )
    is_ngo = any(
        keyword in company or keyword in description
        for keyword in [
            "ngo",
            "non-profit",
            "foundation",
            "charity",
            "united nations",
            "wfp",
        ]
    )

    # Match roles (e.g., "software engineer", "backend developer")
    role_match = any(
        role.lower() in title or role.lower() in description
        for role in resume_keywords["roles"]
    )

    # Match skills (e.g., "python", "django")
    skills_match_count = sum(
        1
        for skill in resume_keywords["skills"]
        if skill.lower() in description or skill.lower() in title
    )
    has_sufficient_skills = skills_match_count >= MIN_SKILL_MATCHES

    # Ensure it's remote, a matching role, has enough skills, and is either international or NGO
    is_relevant = (is_remote and role_match and has_sufficient_skills) and (
        is_international_company or is_ngo
    )

    if is_relevant:
        relevance_score = (
            skills_match_count
            + (2 if is_ngo else 0)
            + (1 if is_international_company else 0)
        )  # Higher score for NGO
        return {
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "url": job_data.get("url"),
            "description": description,
            "date_posted": job_data.get(
                "date_posted", datetime.date.today().isoformat()
            ),
            "date_found": datetime.datetime.now().isoformat(),
            "relevance_score": relevance_score,
        }
    return None


def main():
    """Main function to run the entire job search automation process."""
    print(
        f"--- Job Search Automation started at {datetime.datetime.now().isoformat()} ---"
    )
    setup_database()

    current_run_timestamp = datetime.datetime.now().isoformat()

    # 1. Parse Resume
    resume_keywords = parse_resume_keywords(RESUME_PATH)
    if not resume_keywords:
        print("Could not parse resume or extract keywords. Exiting.")
        return

    all_jobs_found_this_run = []
    new_jobs_for_notification = []

    # Get URLs of already processed jobs from the database to avoid duplicates
    existing_job_urls = get_all_job_urls()
    print(f"Found {len(existing_job_urls)} existing job URLs in the database.")

    # Initialize Selenium driver once for all Selenium-based scraping
    driver = None
    try:
        driver = get_selenium_driver()
    except Exception as e:
        print(f"Failed to initialize Selenium driver: {e}")
        # Continue without Selenium if it fails
        pass

    # 3. Data Collection from various sources using the orchestrator
    print("Starting comprehensive job scraping...")
    unjobs_query = create_search_query(resume_keywords, "unjobs")
    wellfound_query = create_search_query(resume_keywords, "wellfound")

    # Call the master scraping function, passing the driver and specific queries
    all_jobs_found_this_run = scrape_all_jobs(
        driver=driver, unjobs_query=unjobs_query, wellfound_query=wellfound_query
    )
    # The scrape_all_jobs function already prints counts per site and a total.
    time.sleep(SCRAPING_DELAY_SECONDS)  # Add a delay after all scraping is done

    # 4. Filter and Process all collected jobs
    print(f"\nFiltering {len(all_jobs_found_this_run)} total jobs from all sources...")
    for job_data in all_jobs_found_this_run:
        # Check if the job URL already exists in the database
        if job_data.get("url") in existing_job_urls:
            # print(f"Skipping duplicate job: {job_data.get('title')} ({job_data.get('url')})")
            continue  # Skip this job if it's already in the database

        filtered_job = filter_and_process_job(job_data, resume_keywords)
        if filtered_job:
            save_job_listing(filtered_job)
            new_jobs_for_notification.append(filtered_job)
            print(
                f"Saved and marked for notification: {filtered_job['title']} at {filtered_job['company']}"
            )

    # 5. Send Notifications for newly found and relevant jobs
    if new_jobs_for_notification:
        print(
            f"\nSending notifications for {len(new_jobs_for_notification)} new relevant jobs..."
        )
        for job in new_jobs_for_notification:
            send_email_notification(job)
    else:
        print("\nNo new relevant jobs found during this run.")

    # Close the Selenium driver if it was opened
    if driver:
        driver.quit()
        print("Selenium driver closed.")

    print(
        f"--- Job Search Automation finished at {datetime.datetime.now().isoformat()} ---"
    )


if __name__ == "__main__":
    main()
