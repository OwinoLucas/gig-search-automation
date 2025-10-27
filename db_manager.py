# job_search_automation/db_manager.py

import sqlite3

from config import DB_NAME


def setup_database():
    """Initializes the SQLite database and creates the jobs table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            description TEXT,
            date_posted TEXT,
            date_found TEXT,
            relevance_score INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_job_listing(job_data):
    """Saves a job listing to the database. Returns True if saved, False if already exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO jobs (title, company, location, url, description, date_posted, date_found, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_data["title"],
                job_data["company"],
                job_data["location"],
                job_data["url"],
                job_data["description"],
                job_data["date_posted"],
                job_data["date_found"],
                job_data["relevance_score"],
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_jobs_found_since(timestamp_str):
    """Retrieves jobs found after a specific timestamp, ordered by date_posted."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM jobs WHERE date_found > ? ORDER BY date_posted DESC, date_found DESC",
        (timestamp_str,),
    )
    jobs = cursor.fetchall()
    conn.close()
    return jobs


def get_all_job_urls():
    """Retrieves a set of all job URLs currently in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM jobs")
    urls = {row[0] for row in cursor.fetchall()}  # Use a set for efficient lookup
    conn.close()
    return urls


def job_data_to_dict(job_tuple):
    """Converts a job tuple from DB to a dictionary for easier access."""
    # Assuming tuple structure: (id, title, company, location, url, description, date_posted, date_found, relevance_score)
    return {
        "id": job_tuple[0],
        "title": job_tuple[1],
        "company": job_tuple[2],
        "location": job_tuple[3],
        "url": job_tuple[4],
        "description": job_tuple[5],
        "date_posted": job_tuple[6],
        "date_found": job_tuple[7],
        "relevance_score": job_tuple[8],
    }
