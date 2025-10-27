# job_search_automation/job_scraper.py

import datetime
import re
import time

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    REQUESTS_HEADERS,  # Assuming REQUESTS_HEADERS includes User-Agent etc.
)


# --- Helper Function for Selenium Description Fetch ---
def fetch_full_description_selenium(driver, job_url):
    """Attempts to fetch full job description from a URL using Selenium."""
    if not driver:
        print(f"No Selenium driver provided for {job_url}.")
        return "N/A (Selenium driver not available)"
    if not job_url or job_url == "N/A":
        return "No URL provided."

    print(f"Attempting to fetch full description for: {job_url} (Selenium)")
    try:
        driver.get(job_url)
        # Wait for the description content to be present. Adjust selector if needed.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div[class*="description"], div[class*="content"], div[class*="job-details"]',
                )
            )
        )
        time.sleep(2)  # Give a little extra time for dynamic content

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Generic selectors - highly site-specific. Needs refinement for each site.
        description_elements = soup.find_all(
            ["div", "p", "li", "span"],
            class_=lambda x: x
            and (
                "description" in x.lower()
                or "content" in x.lower()
                or "job-details" in x.lower()
            ),
        )
        if not description_elements:
            description_elements = soup.find_all(["div", "p", "li"])  # Broader fallback

        description_text = " ".join(
            [
                elem.get_text(strip=True)
                for elem in description_elements
                if elem.get_text(strip=True)
            ]
        )
        return description_text[:5000]  # Truncate to 5000 characters
    except (TimeoutException, WebDriverException) as e:
        print(
            f"Failed to fetch description from {job_url} with Selenium (WebDriver error): {e}"
        )
    except Exception as e:
        print(f"Error parsing description from {job_url} with Selenium: {e}")
    return "N/A (Could not fetch full description via Selenium)"


def fetch_full_description_requests(job_url):
    """
    Attempts to fetch full job description from a URL using requests.
    This version is generic; for specific sites like careers.un.org,
    it might need more tailored selectors within the function.
    """
    if not job_url or job_url == "N/A":
        return "No URL provided."
    try:
        print(f"Attempting to fetch full description for: {job_url} (Requests)")
        time.sleep(1)  # Be polite
        response = requests.get(job_url, headers=REQUESTS_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Specific selectors for careers.un.org for its internal description pages
        # You MUST verify these by inspecting a job detail page on careers.un.org
        description_div = soup.select_one(
            "#job-description-text, div.job-detail-content, div[itemprop='description'], .panel-body.job-description"
        )
        if description_div:
            return description_div.get_text(separator="\n", strip=True)[
                :5000
            ]  # Truncate

        # Generic selectors - fallback if site-specific ones don't match or for other sites
        description_elements = soup.find_all(
            ["div", "p", "li", "span"],
            class_=lambda x: x
            and (
                "description" in x.lower()
                or "content" in x.lower()
                or "job-details" in x.lower()
            ),
        )

        if not description_elements:
            description_elements = soup.find_all(["div", "p", "li"])

        description_text = " ".join(
            [
                elem.get_text(strip=True)
                for elem in description_elements
                if elem.get_text(strip=True)
            ]
        )
        return description_text[:5000]  # Truncate to 5000 characters
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch description from {job_url} with requests: {e}")
    except Exception as e:
        print(f"Error parsing description from {job_url} with requests: {e}")
    return "N/A (Could not fetch full description via requests)"


def scrape_wellfound(driver, query):
    """
    Scrapes Wellfound (formerly AngelList Talent) for jobs using Selenium for the main page
    and potentially for description fetching.
    """
    print(f"\nScraping Wellfound for query: {query}")
    # Construct the base URL for the job search
    params = {
        "q": query,
        "remote": "true",  # Keep this if you only want remote jobs
    }
    # Use requests.Request to properly encode URL parameters, but then pass to Selenium
    full_url = (
        requests.Request("GET", "https://wellfound.com/jobs", params=params)
        .prepare()
        .url
    )

    jobs = []
    if not driver:
        print("Selenium driver not provided for Wellfound. Cannot scrape dynamically.")
        return jobs

    try:
        driver.get(full_url)
        # Give the page time to load dynamic content. Increase if needed.
        time.sleep(5)

        # You might need to scroll to load more jobs if Wellfound uses infinite scrolling
        # For simplicity, let's just get the initial load's content for now.
        # If you need to scroll:
        # last_height = driver.execute_script("return document.body.scrollHeight")
        # while True:
        #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #     time.sleep(3) # Wait for new content to load
        #     new_height = driver.execute_script("return document.body.scrollHeight")
        #     if new_height == last_height:
        #         break
        #     last_height = new_height
        # time.sleep(2) # Final wait

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # --- Updated Wellfound Selectors (these are still subject to change by Wellfound) ---
        # Look for general job card structure
        job_cards = soup.select(
            'div[data-test="JobCard"]'
        )  # Common attribute on Wellfound
        if not job_cards:
            # Fallback to a class regex if data-test attribute changes
            job_cards = soup.find_all("div", class_=re.compile(r"styles_jobCard"))
            if not job_cards:
                print(
                    "No job cards found using either data-test or class regex for Wellfound."
                )

        for job_card in job_cards:
            try:
                # Titles are usually in h2 or h3 with specific data-test or class
                title_tag = job_card.select_one(
                    'h2[data-test="job-card-title"], h3[data-test="job-card-title"], h2[class*="title"], h3[class*="title"]'
                )
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                # Company names can be in div, a, or span
                company_tag = job_card.select_one(
                    'div[data-test="job-card-company-name"], a[data-test="JobCard_companyLink"]'
                )
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                # Location can be in div or span
                location_tag = job_card.select_one(
                    'div[data-test="job-card-location"], span[class*="location"]'
                )
                location = location_tag.get_text(strip=True) if location_tag else "N/A"

                # Job URL link
                job_url_tag = job_card.select_one(
                    'a[data-test="JobCard_link"], a[href*="/jobs/"]'
                )
                job_url = (
                    "https://wellfound.com" + job_url_tag["href"]
                    if job_url_tag and "href" in job_url_tag.attrs
                    else "N/A"
                )

                # Fetch description - try requests first, fallback to Selenium if requests fails
                description = fetch_full_description_requests(job_url)
                if (
                    "N/A (Could not fetch" in description and driver
                ):  # Check if requests failed
                    description = fetch_full_description_selenium(driver, job_url)
                elif "N/A (Could not fetch" in description and not driver:
                    description = "N/A (Could not fetch description, Selenium driver not available for fallback)"

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "description": description,
                        "date_posted": datetime.date.today().isoformat(),  # Wellfound doesn't always show explicit date_posted on listing
                    }
                )
            except Exception as e:
                print(f"Error parsing a Wellfound job card: {e}")
                continue  # Continue to next job card even if one fails

        print(f"Found {len(jobs)} jobs on Wellfound.")
    except Exception as e:
        print(f"Error scraping Wellfound (general): {e}")
    return jobs


# --- Helper to get the FINAL application URL from unjobs.org's vacancy page ---
def get_unjobs_application_url(vacancy_page_url):
    """
    Navigates to the unjobs.org vacancy page (e.g., https://unjobs.org/vacancies/...)
    and extracts the 'Apply' button's href, which is the actual application URL.
    """
    if not vacancy_page_url or "unjobs.org/vacancies" not in vacancy_page_url:
        return "N/A"

    try:
        response = requests.get(vacancy_page_url, headers=REQUESTS_HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Look for the 'Apply' button/link. Common selectors:
        # 1. A link with specific text (case-insensitive)
        # 2. A button with specific text/class
        apply_link = soup.find(
            "a", class_="btn", text=re.compile(r"apply|more info", re.IGNORECASE)
        )
        if not apply_link:
            # Fallback to broader selector for typical apply links
            apply_link = soup.select_one("a[href*='apply.'], a[href*='careers.']")

        if apply_link and "href" in apply_link.attrs:
            return apply_link["href"].strip()
        else:
            print(f"Warning: Could not find 'Apply' link on {vacancy_page_url}")
            return "N/A"

    except requests.exceptions.RequestException as e:
        print(f"Error fetching UNJobs vacancy page {vacancy_page_url}: {e}")
        return "N/A"
    except Exception as e:
        print(f"Error parsing UNJobs vacancy page {vacancy_page_url}: {e}")
        return "N/A"


# --- Scraper for unjobs.org ---
def scrape_unjobs_org(query):
    """
    Scrapes unjobs.org for high-level job details and the direct application link.
    Focuses on 'software development' related queries.
    """
    print(f"\nScraping unjobs.org for query: {query}")
    search_url = f"https://unjobs.org/?q={requests.utils.quote(query)}"
    jobs = []
    try:
        response = requests.get(search_url, headers=REQUESTS_HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Select all job cards on the search results page
        job_cards = soup.select("div.card.mb-3")
        if not job_cards:
            # Fallback for alternative structures if initial selector fails
            job_cards = soup.find_all(
                "div", class_=re.compile(r"job-card|listing-card")
            )
            if not job_cards:
                print(
                    "No job cards found on unjobs.org. Check selectors or page structure."
                )

        for card in job_cards:
            try:
                # Title and UNJobs internal vacancy URL
                title_tag = card.select_one("h5.card-title a, h4.card-title a")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                unjobs_vacancy_url = (
                    title_tag["href"]
                    if title_tag and "href" in title_tag.attrs
                    else "N/A"
                )
                if unjobs_vacancy_url.startswith("/"):
                    unjobs_vacancy_url = "https://unjobs.org" + unjobs_vacancy_url

                # Company
                company_tag = card.select_one("h6.card-subtitle, .job-agency")
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                # Location
                location_tag = card.select_one(
                    "i.bi-geo-alt-fill + span, .job-location-text"
                )
                location = location_tag.get_text(strip=True) if location_tag else "N/A"

                # Date Posted (Robust parsing needed)
                date_tag = card.select_one("span.text-muted small, .job-posted-date")
                date_posted_str = date_tag.get_text(strip=True) if date_tag else None
                date_posted = datetime.date.today().isoformat()  # Default to today

                if date_posted_str:
                    # Example: "X days ago"
                    match_days = re.search(
                        r"(\d+)\s+days?\s+ago", date_posted_str, re.IGNORECASE
                    )
                    if match_days:
                        days_ago = int(match_days.group(1))
                        date_posted = (
                            datetime.date.today() - datetime.timedelta(days=days_ago)
                        ).isoformat()
                    else:
                        # Example: "Month Day, Year" or "DD Month Year"
                        try:
                            date_obj = datetime.datetime.strptime(
                                date_posted_str.replace(",", ""), "%B %d %Y"
                            ).date()
                            date_posted = date_obj.isoformat()
                        except ValueError:
                            try:
                                date_obj = datetime.datetime.strptime(
                                    date_posted_str, "%d %B %Y"
                                ).date()
                                date_posted = date_obj.isoformat()
                            except ValueError:
                                # Fallback if no specific format matches
                                pass

                # Get the actual application URL by visiting the unjobs.org vacancy page
                actual_application_url = get_unjobs_application_url(unjobs_vacancy_url)

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": actual_application_url,  # Store the actual application link
                        "description": "Aggregator listing - refer to external URL for full details.",  # Placeholder description
                        "date_posted": date_posted,
                    }
                )
            except Exception as e:
                print(f"Error parsing a UNJobs job card (query: '{query}'): {e}")
                continue

        print(f"Found {len(jobs)} jobs on unjobs.org for '{query}'.")
    except requests.exceptions.RequestException as e:
        print(f"Error scraping unjobs.org for '{query}': {e}")
    except Exception as e:
        print(f"Error parsing unjobs.org HTML (general) for '{query}': {e}")
    return jobs


# --- Scraper for careers.un.org ---
def scrape_careers_un_org(query=None):  # Query might be optional/less direct here
    """
    Scrapes careers.un.org specifically for IT-related jobs.
    Uses a predefined URL for IT jobs and fetches full descriptions.
    """
    print("\nScraping careers.un.org for IT jobs.")
    # This URL is directly provided and filters for IT-related jobs.
    # The 'query' parameter for this function might be used to further filter results
    # if careers.un.org supports additional URL parameters, otherwise it's ignored for this specific base URL.
    base_url = "https://careers.un.org/jobopening"
    # The 'data' parameter is a URL-encoded JSON object for filters
    it_filter_data = '{"jf":["IST"],"jn":["ITECNET"]}'  # Job Family: Information Systems and Technology, Job Network: ITECNET
    # If there's an additional keyword query, you might append it to 'data' parameter
    # For now, we'll stick to the provided IT filter.
    url = f"{base_url}?data={requests.utils.quote(it_filter_data)}"

    jobs = []
    try:
        response = requests.get(url, headers=REQUESTS_HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # --- IMPORTANT: Inspect careers.un.org to get correct selectors ---
        # Based on inspecting careers.un.org (as of late 2023 / early 2024),
        # jobs are typically within a div with id 'searchResultPanel' or a table.
        # Let's try to be robust.

        # A common pattern is a table inside the search results panel
        # Looking for table rows or specific cards within the search result area.
        job_rows = soup.select(
            "div#searchResultPanel table tbody tr.row, div#job-openings-table tbody tr"
        )

        if not job_rows:
            print(
                "No job rows found on careers.un.org using initial selectors. Trying broader search."
            )
            # Fallback to broader search if initial is too specific
            job_rows = soup.select(
                "div.job-listing-card, li.job-item"
            )  # More generic card/list item
            if not job_rows:
                print("No job cards/rows found using broader selectors either.")
                # You may need to manualy inspect the site and find the correct parent container

        for row in job_rows:
            try:
                # Assuming job details are in columns (<td>) or specific child elements of the row/card

                # Title and internal job URL
                # The title might be in a strong tag within an anchor, or a direct anchor.
                title_tag = row.select_one(
                    "td:nth-child(1) a, h3.job-title a"
                )  # e.g., first column link
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                job_url = (
                    "https://careers.un.org" + title_tag["href"]
                    if title_tag and "href" in title_tag.attrs
                    else "N/A"
                )

                company = "United Nations"  # Consistent for this site

                # Location (Duty Station) - often in the second or third column
                location_tag = row.select_one(
                    "td:nth-child(3), .job-location span"
                )  # e.g., third column
                location = location_tag.get_text(strip=True) if location_tag else "N/A"

                # Posting Period (Date Posted) - often in the last column
                # This might be a range (e.g., "DD Month YYYY - DD Month YYYY")
                date_str_tag = row.select_one(
                    "td:last-child, .job-posted-date"
                )  # e.g., last column
                date_posted_str = (
                    date_str_tag.get_text(strip=True) if date_str_tag else None
                )
                date_posted = datetime.date.today().isoformat()  # Default

                if date_posted_str:
                    # Example: "24 July 2023 - 23 August 2023" or similar
                    # Extract start date for 'date_posted' field
                    match_date_range = re.match(
                        r"(\d{1,2}\s+\w+\s+\d{4})", date_posted_str
                    )
                    if match_date_range:
                        try:
                            date_obj = datetime.datetime.strptime(
                                match_date_range.group(1), "%d %B %Y"
                            ).date()
                            date_posted = date_obj.isoformat()
                        except ValueError:
                            pass  # Keep default if parsing fails

                # Fetch full description as it's internal
                description = fetch_full_description_requests(job_url)

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "description": description,
                        "date_posted": date_posted,
                    }
                )
            except Exception as e:
                print(f"Error parsing a careers.un.org job row: {e}")
                continue

        print(f"Found {len(jobs)} IT jobs on careers.un.org.")

    except requests.exceptions.RequestException as e:
        print(f"Error scraping careers.un.org: {e}")
    except Exception as e:
        print(f"Error parsing careers.un.org HTML (general): {e}")
    return jobs


# --- Master Function to orchestrate all scrapers ---
def scrape_all_jobs(
    driver, unjobs_query="software development", wellfound_query="software engineer"
):
    """
    Orchestrates scraping from multiple job boards.
    Args:
        driver: Selenium WebDriver instance (for sites requiring dynamic loading).
        unjobs_query (str): The search query for unjobs.org.
        wellfound_query (str): The search query for wellfound.com.
    Returns:
        list: A combined list of job dictionaries from all sources.
    """
    all_jobs = []

    # Scrape unjobs.org
    unjobs_jobs = scrape_unjobs_org(unjobs_query)
    all_jobs.extend(unjobs_jobs)

    # Scrape careers.un.org (no direct query needed, uses pre-filtered URL)
    careers_jobs = (
        scrape_careers_un_org()
    )  # Query param is ignored for this specific base URL
    all_jobs.extend(careers_jobs)

    # Scrape Wellfound (requires Selenium driver)
    wellfound_jobs = scrape_wellfound(driver, wellfound_query)
    all_jobs.extend(wellfound_jobs)

    # LinkedIn is skipped
    linkedin_jobs = scrape_linkedin_jobs(None)
    all_jobs.extend(linkedin_jobs)

    print(f"\nTotal jobs found from all sources: {len(all_jobs)}")
    return all_jobs


def scrape_linkedin_jobs(query):
    print(
        "\nLinkedIn scraping is highly restricted and against Terms of Service. Skipping."
    )
    return []
