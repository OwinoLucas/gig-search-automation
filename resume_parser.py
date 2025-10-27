# job_search_automation/resume_parser.py

import os

from pdfminer.high_level import extract_text

from config import DEFAULT_PREFERENCES, DEFAULT_ROLES, DEFAULT_SKILLS


def parse_resume_keywords(pdf_path):
    """
    Extracts text from a PDF resume and identifies relevant keywords.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: Resume file not found at {pdf_path}")
        return {}

    try:
        text = extract_text(pdf_path)
    except Exception as e:
        print(f"Error parsing PDF resume with pdfminer.six: {e}")
        return {}

    text_lower = text.lower()

    # Use default keywords if not explicitly found, or enhance them
    extracted_skills = [skill for skill in DEFAULT_SKILLS if skill in text_lower]
    extracted_roles = [role for role in DEFAULT_ROLES if role in text_lower]
    # Preferences are generally high-level and might not be explicitly in resume text,
    # but could be inferred or set as static config.

    print(
        f"Resume keywords extracted: Skills={extracted_skills}, Roles={extracted_roles}"
    )
    return {
        "skills": list(set(extracted_skills)),
        "roles": list(set(extracted_roles)),
        "preferences": DEFAULT_PREFERENCES,  # Default preferences, as they are general search criteria
    }


def create_search_query(keywords, platform_name):
    """
    Generates a search query string based on keywords for a specific platform.
    This can be customized per platform if their search syntax differs.
    """
    # Basic query construction
    role_terms = " OR ".join(keywords["roles"])
    skill_terms = " OR ".join(keywords["skills"])

    base_query = f"{role_terms} {skill_terms}"

    # Platform-specific adjustments (examples)
    if platform_name == "wellfound":
        return "+".join(keywords["roles"] + keywords["skills"]) + "+remote"
    elif platform_name == "microsoft":
        search_terms = "%20".join(keywords["roles"] + keywords["skills"])
        # Location is often handled directly in Selenium, or specific to query params
        return f"q={search_terms}&lc=Nairobi%2C%20Nairobi%20City%2C%20Kenya"
    elif platform_name == "wfp":
        # Workday has its own search input fields, so a single query string is less relevant
        return keywords["roles"] + keywords["skills"] + ["remote"]
    elif platform_name in ["unjobs", "un_careers"]:
        return " ".join(
            keywords["roles"] + keywords["skills"] + ["remote", "ngo", "united nations"]
        )

    return base_query
