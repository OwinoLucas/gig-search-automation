# job_search_automation/config.py
from decouple import config

# --- General Configuration ---
RESUME_PATH = config(
    "RESUME_PATH"
)  # Default; can be overridden by .env or command line

# --- Database Configuration ---
DB_NAME = config("DB_NAME")

# --- Web Scraping Configuration ---
REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Upgrade-Insecure-Requests": "1",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
}
SCRAPING_DELAY_SECONDS = int(config("SCRAPING_DELAY_SECONDS"))
print("SCRAPING_DELAY_SECONDS:", SCRAPING_DELAY_SECONDS)
# Delay between scraping different websites

# --- Keywords and Preferences (default values, can be enhanced by resume parsing) ---
DEFAULT_SKILLS = [
    "python",
    "django",
    "flask",
    "aws",
    "docker",
    "kubernetes",
    "sql",
    "rest api",
    "microservices",
    "git",
    "linux",
    "cloud",
    "api design",
]
DEFAULT_ROLES = [
    "software engineer",
    "backend developer",
    "software developer",
    "devops engineer",
    "cloud engineer",
]
DEFAULT_PREFERENCES = ["remote", "international", "ngo", "non-profit", "worldwide"]

# --- Filtering Thresholds ---
MIN_SKILL_MATCHES = int(config("MIN_SKILL_MATCHES"))
