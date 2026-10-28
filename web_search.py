from duckduckgo_search import DDGS
from typing import List, Dict, Any


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query to look up
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        A list of dictionaries containing title, url, and snippet for each result
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
        return results
    except Exception as e:
        return [{"title": "Error", "url": "", "snippet": str(e)}]
