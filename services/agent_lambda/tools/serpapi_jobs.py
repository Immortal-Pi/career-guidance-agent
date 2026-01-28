import os
import requests

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

def serpapi_google_jobs(query: str, location: str = "Dallas, TX", num_results: int = 8) -> dict:
    if not SERPAPI_KEY:
        return {"error": "SERPAPI_KEY not set"}

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_KEY,
    }

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    # Normalize top jobs
    jobs = []
    for j in (data.get("jobs_results") or [])[:num_results]:
        jobs.append({
            "title": j.get("title"),
            "company": j.get("company_name"),
            "location": j.get("location"),
            "via": j.get("via"),
            "posted_at": j.get("detected_extensions", {}).get("posted_at"),
            "description_snippet": j.get("description"),
            "apply_links": j.get("apply_options"),
        })

    return {
        "query": query,
        "location": location,
        "jobs": jobs
    }
