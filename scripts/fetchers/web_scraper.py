import requests
import re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_web_scrape_section(section_id, section_config, max_per_site=3):
    items = []
    for site in section_config.get("sites", []):
        try:
            fetched = scrape_site(site, max_per_site)
            items.extend(fetched)
            print(f"  [OK] {site['source']}: {len(fetched)} items")
        except Exception as e:
            print(f"  [FAIL] {site['source']}: {e}")
    return {
        "id": section_id,
        "name": section_config["name"],
        "items": items,
    }


def scrape_site(site_cfg, max_items=3):
    source = site_cfg["source"]
    url = site_cfg["url"]

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        raise Exception(f"HTTP error: {e}")

    if source == "a16z":
        return parse_a16z(html, max_items)
    elif source == "CB Insights - AI":
        return parse_cb_insights(html, max_items)
    elif source == "Way to AGI":
        return parse_waytoagi(html, max_items)
    else:
        return []


def parse_a16z(html, max_items):
    items = []
    pattern = r'<a[^>]*href="(https://a16z\.com/[^"]+)"[^>]*>\s*<h[234][^>]*>([^<]+)</h'
    matches = re.findall(pattern, html)

    for url, title in matches[:max_items]:
        title = title.strip()
        if not title or len(title) < 10:
            continue
        items.append({
            "source": "a16z",
            "title": title,
            "summary": "",
            "url": url,
            "time": "",
            "eventId": None,
            "relatedDate": None,
        })
    return items


def parse_cb_insights(html, max_items):
    items = []
    pattern = r'<a[^>]*href="(https://www\.cbinsights\.com/research/[^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html)

    for url, title in matches[:max_items]:
        title = title.strip()
        if not title or len(title) < 10:
            continue
        items.append({
            "source": "CB Insights - AI",
            "title": title,
            "summary": "",
            "url": url,
            "time": "",
            "eventId": None,
            "relatedDate": None,
        })
    return items


def parse_waytoagi(html, max_items):
    items = []
    pattern = r'<a[^>]*href="([^"]*)"[^>]*>\s*<[^>]*>([^<]{15,})</[^>]*>\s*</a>'
    matches = re.findall(pattern, html)

    for url, title in matches[:max_items]:
        title = title.strip()
        if not url.startswith("http"):
            url = "https://www.waytoagi.com" + url
        items.append({
            "source": "Way to AGI",
            "title": title,
            "summary": "",
            "url": url,
            "time": "",
            "eventId": None,
            "relatedDate": None,
        })
    return items
