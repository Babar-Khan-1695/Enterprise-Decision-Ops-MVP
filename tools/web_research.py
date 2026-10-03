"""Best-effort DuckDuckGo HTML research for decision-relevant external evidence."""
import html
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus, unquote, urlparse
from urllib.request import Request, urlopen


def _clean_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def search_web(query, max_results=5):
    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 Enterprise-DecisionOps/1.0"})
        with urlopen(req, timeout=8) as response:
            page = response.read().decode("utf-8", errors="ignore")
        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<div class="result|</div>\s*</div>)',
            re.I | re.S
        )
        for match in pattern.finditer(page):
            href = html.unescape(match.group(1))
            title = _clean_html(match.group(2))
            block = match.group(3)
            snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</', block, re.I | re.S)
            snippet = _clean_html(snippet_match.group(1)) if snippet_match else ""
            if "uddg=" in href:
                encoded = re.search(r"uddg=([^&]+)", href)
                if encoded:
                    href = unquote(encoded.group(1))
            if href.startswith("//"):
                href = "https:" + href
            if href and title and urlparse(href).scheme in ("http", "https"):
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "accessed_at": datetime.now(timezone.utc).isoformat(),
                })
            if len(results) >= max_results:
                break
        return results
    except Exception as exc:
        return [{
            "title": "External web search unavailable",
            "url": "",
            "snippet": f"Search could not be completed: {exc}",
            "accessed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }]


def research_for_decision(title, objective, constraints):
    text = f"{title}. {objective}. {constraints}"
    lower = text.lower()
    location_terms = [
        "lahore", "location", "area", "site", "facility", "distribution center",
        "warehouse", "branch", "new business", "market entry", "property"
    ]
    queries = []
    if any(k in lower for k in location_terms):
        queries.append(f"{title} Lahore location area market infrastructure business site suitability")
        queries.append(f"{objective[:250]} location competitors logistics infrastructure risks")
    else:
        queries.append(f"{title} industry market business risks")
        queries.append(f"{objective[:300]} external market evidence industry")
    results = []
    for query in queries:
        for item in search_web(query, 4):
            if item.get("url") and not any(x["url"] == item["url"] for x in results):
                results.append(item)
    return results[:8]
