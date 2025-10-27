# 🚀 Automated Job Search Script

This project provides an automated solution for scanning job boards, filtering opportunities based on your resume keywords and specified criteria, and notifying you of relevant postings via email. It's designed to help you efficiently find remote, international, or NGO job opportunities that align with your profile.

## ✨ Features

- **Resume-driven Filtering:** Automatically parses your resume to extract key skills and roles, using them to intelligently filter job listings.
- **Multi-Platform Scraping:** Gathers job data from various online sources (e.g., Wellfound, UNJobs.org, with extensibility for LinkedIn, Indeed, etc.).
- **Customizable Job Matching:** Filters jobs based on criteria like remote status, international company presence, NGO affiliation, and a minimum number of skill matches.
- **Database Storage:** Stores relevant job postings in a local SQLite database, preventing duplicates and allowing for historical tracking.
- **Email Notifications:** Sends email alerts for new job postings that meet your specific requirements.
- **Selenium Integration:** Uses Selenium for dynamic website scraping where necessary, allowing interaction with JavaScript-rendered content.

## 🛠️ Technologies Used

- **Python 3.12.6**
- **BeautifulSoup4:** For parsing HTML content.
- **Requests:** For making HTTP requests to job boards.
- **Selenium:** For browser automation (e.g., dynamic content loading, navigating pages).
- **Pandas (optional, for data processing/analysis):** If you decide to add more advanced data handling.
- **SQLite:** For local database storage.
- **`python-dotenv`:** For managing environment variables securely.
- **`smtplib`:** For sending email notifications.

## 📋 Setup & Installation

Follow these steps to get your job search script up and running.

### 1. Clone the Repository

```bash
git clone https://github.com/OwinoLucas/gig-search-automation.git
cd gig-search-automation
```
