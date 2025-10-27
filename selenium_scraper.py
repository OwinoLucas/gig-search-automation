# job_search_automation/selenium_scraper.py

import datetime
import os

from dotenv import load_dotenv  # To load CHROMEDRIVER_PATH
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import REQUESTS_HEADERS  # For user agent

load_dotenv()  # Load environment variables

CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", None)


def get_selenium_driver():
    """Initializes and returns a Selenium WebDriver (Chrome in headless mode)."""
    options = webdriver.ChromeOptions()
    options.add_argument(
        "--headless"
    )  # Run in background without opening browser window
    options.add_argument("--no-sandbox")  # Needed for root user in some environments
    options.add_argument(
        "--disable-dev-shm-usage"
    )  # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080")  # Set a reasonable window size
    options.add_argument(
        "user-agent=" + REQUESTS_HEADERS["User-Agent"]
    )  # Set user agent for Selenium

    try:
        if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
            service = Service(CHROMEDRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Assumes chromedriver is in system PATH if CHROMEDRIVER_PATH is not set or not found
            driver = webdriver.Chrome(options=options)
        print("Selenium WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        print(f"Error initializing WebDriver: {e}")
        print(
            "Please ensure ChromeDriver is installed and its path is correctly set in CHROMEDRIVER_PATH environment variable or in your system's PATH."
        )
        return None


def fetch_full_description_selenium(driver, job_url):
    """Attempts to fetch full job description from a URL using Selenium."""
    if not driver:
        return "No Selenium driver available."
    if not job_url or job_url == "N/A":
        return "No URL provided."
    try:
        print(f"Attempting to fetch full description for (Selenium): {job_url}")
        driver.get(job_url)
        # Wait for the main job description content to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )

        # Site-specific selectors for job description content. Add more as needed.
        description_elements = driver.find_elements(
            By.CSS_SELECTOR,
            ".job-description-content, .job-details, [data-automation-id='jobDescription'], #job_description_body, .description__text, .richText",
        )

        if description_elements:
            description_text = " ".join(
                [elem.text.strip() for elem in description_elements]
            )
        else:
            # Fallback to a common content div or even body text
            try:
                main_content_div = driver.find_element(
                    By.CSS_SELECTOR, ".wd-main-content, #main-content"
                )
                description_text = main_content_div.text.strip()
            except NoSuchElementException:
                description_text = driver.find_element(
                    By.CSS_SELECTOR, "body"
                ).text.strip()  # Last resort

        return description_text[:5000]  # Truncate
    except TimeoutException:
        print(f"Timeout fetching description for {job_url} with Selenium.")
    except NoSuchElementException:
        print(f"Could not find description elements for {job_url} with Selenium.")
    except Exception as e:
        print(f"Error fetching description from {job_url} with Selenium: {e}")
    return "N/A (Could not fetch full description via Selenium)"


def scrape_microsoft_careers(driver, query_params, location_name="Nairobi"):
    """
    Scrapes Microsoft Careers using Selenium due to its highly dynamic nature.
    """
    if not driver:
        print("Microsoft Careers scraping skipped: Selenium driver not initialized.")
        return []

    print(
        f"Scraping Microsoft Careers for query params: {query_params}, location: {location_name}"
    )
    url = f"https://jobs.careers.microsoft.com/global/en/search?{query_params}"
    jobs = []
    try:
        driver.get(url)
        # Wait for job cards to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.job-card"))
        )

        job_listings = driver.find_elements(By.CSS_SELECTOR, "li.job-card")
        print(f"Found {len(job_listings)} raw job cards on Microsoft Careers.")

        for job_card in job_listings:
            try:
                title_elem = job_card.find_element(By.CSS_SELECTOR, "h3.job-title")
                job_url_elem = job_card.find_element(By.CSS_SELECTOR, "a.job-link")
                location_elem = job_card.find_element(
                    By.CSS_SELECTOR, "span.job-location"
                )

                title = title_elem.text.strip()
                job_url = job_url_elem.get_attribute("href")
                location = location_elem.text.strip()
                company = "Microsoft"  # Hardcoded

                description = fetch_full_description_selenium(
                    driver, job_url
                )  # Fetch description with Selenium

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "description": description,
                        "date_posted": datetime.date.today().isoformat(),  # Placeholder
                    }
                )
            except NoSuchElementException:
                # print("Skipping a Microsoft job card due to missing elements.")
                continue
            except Exception as e:
                print(f"Error processing a Microsoft job card: {e}")
                continue
        print(f"Processed {len(jobs)} jobs from Microsoft Careers.")
    except TimeoutException:
        print("Timeout waiting for Microsoft Careers job listings to load.")
    except WebDriverException as e:
        print(f"WebDriver error during Microsoft Careers scraping: {e}")
    except Exception as e:
        print(f"Error scraping Microsoft Careers: {e}")
    return jobs


def scrape_wfp_careers(driver, keywords):
    """
    Scrapes WFP Careers (Workday) using Selenium. This requires interacting with search fields.
    """
    if not driver:
        print("WFP Careers scraping skipped: Selenium driver not initialized.")
        return []

    print(f"Scraping WFP Careers for keywords: {keywords}")
    url = "https://wd3.myworkdaysite.com/recruiting/wfp/job_openings"
    jobs = []
    try:
        driver.get(url)

        # Wait for the search input field to be present
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//input[contains(@aria-label, 'Search') or @data-automation-id='searchText']",
                )
            )
        )

        search_input = driver.find_element(
            By.XPATH,
            "//input[contains(@aria-label, 'Search') or @data-automation-id='searchText']",
        )
        search_input.send_keys(" ".join(keywords))
        search_input.send_keys(
            webdriver.common.keys.Keys.RETURN
        )  # Simulate pressing Enter

        # Wait for job listings to load after search
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[contains(@data-automation-id, 'compositeJobCard')]")
            )
        )

        job_listings = driver.find_elements(
            By.XPATH, "//li[contains(@data-automation-id, 'compositeJobCard')]"
        )
        print(f"Found {len(job_listings)} raw job cards on WFP Careers.")

        for job_card in job_listings:
            try:
                title_elem = job_card.find_element(
                    By.XPATH, ".//h3[contains(@data-automation-id, 'jobTitle')]"
                )
                job_url_elem = title_elem.find_element(By.TAG_NAME, "a")
                company = "World Food Programme"  # Hardcoded
                location_elem = job_card.find_element(
                    By.XPATH, ".//div[contains(@data-automation-id, 'locationsText')]"
                )

                title = title_elem.text.strip()
                job_url = job_url_elem.get_attribute("href")
                location = location_elem.text.strip()

                description = fetch_full_description_selenium(
                    driver, job_url
                )  # Fetch description with Selenium

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_url,
                        "description": description,
                        "date_posted": datetime.date.today().isoformat(),  # Placeholder
                    }
                )
            except NoSuchElementException:
                # print("Skipping a WFP job card due to missing elements.")
                continue
            except Exception as e:
                print(f"Error processing a WFP job card: {e}")
                continue
        print(f"Processed {len(jobs)} jobs from WFP Careers.")
    except TimeoutException:
        print("Timeout waiting for WFP Careers job listings to load.")
    except WebDriverException as e:
        print(f"WebDriver error during WFP Careers scraping: {e}")
    except Exception as e:
        print(f"Error scraping WFP Careers: {e}")
    return jobs
