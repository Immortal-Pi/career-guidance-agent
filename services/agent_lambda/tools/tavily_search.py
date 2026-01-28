import os
import requests

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_SEARCH_ENDPOINT = "https://api.tavily.com/search"

def tavily_web_search(query: str, max_results: int = 5) -> dict:
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not set"}

    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "query": query,
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": False,
    }

    r = requests.post(TAVILY_SEARCH_ENDPOINT, headers=headers, json=body, timeout=25)
    r.raise_for_status()
    return r.json()
