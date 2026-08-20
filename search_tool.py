

from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
from config import RESULTS_PER_QUERY, MAX_CHARS_PER_PAGE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def search_web(query: str, max_results: int = RESULTS_PER_QUERY) -> list[dict]:
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        print(f"[search_web] search failed for '{query}': {e}")
    return results


def fetch_page_text(url: str, max_chars: int = MAX_CHARS_PER_PAGE) -> str:
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # strip noisy elements that aren't real content
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()

        # prefer <article> or <main> if present, else fall back to full body
        container = soup.find("article") or soup.find("main") or soup.body or soup
        text = container.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        print(f"[fetch_page_text] failed for {url}: {e}")
        return ""


def search_and_gather(query: str, max_results: int = RESULTS_PER_QUERY) -> list[dict]:
    hits = search_web(query, max_results)
    gathered = []
    for hit in hits:
        content = fetch_page_text(hit["url"])
        gathered.append({**hit, "content": content})
    return gathered