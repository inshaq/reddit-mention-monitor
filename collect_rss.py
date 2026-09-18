"""Keyless collector: Reddit's public search RSS feeds. Posts only (no comments), ~25 per query.

Low-volume personal use only. Requests are spaced out to stay under Reddit's rate limits.
"""
import html
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

import requests

import collect
import config
import db

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
NS = {"a": "http://www.w3.org/2005/Atom"}
DELAY = 8  # seconds between requests


def feed_urls():
    for q in config.SEARCH_QUERIES:
        yield f"https://www.reddit.com/search.rss?q={quote_plus(q)}&sort=new&t=year"
    for s in config.SUBREDDITS:
        yield f"https://www.reddit.com/r/{s}/search.rss?q={quote_plus(config.PRIMARY_TERM)}&restrict_sr=1&sort=new&t=year"


def strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()


def fetch(url: str):
    for attempt in range(3):
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code == 200:
            return ET.fromstring(r.content)
        if r.status_code == 429:
            time.sleep(30 * (attempt + 1))
            continue
        print(f"  {r.status_code} for {url}")
        return None
    print(f"  gave up (rate limited): {url}")
    return None


def entries(root):
    for e in root.findall("a:entry", NS):
        link = e.find("a:link", NS).get("href")
        cat = e.find("a:category", NS)
        title = e.findtext("a:title", "", NS)
        body = strip_html(e.findtext("a:content", "", NS))
        ts = datetime.fromisoformat(e.findtext("a:updated", "", NS)).timestamp()
        yield {
            "id": "rss_" + link.rstrip("/").split("/comments/")[-1].split("/")[0],
            "kind": "post",
            "subreddit": cat.get("term") if cat is not None else "",
            "title": title,
            "body": body,
            "url": link,
            "score": 0,  # RSS doesn't expose score
            "created_utc": ts,
        }


def run():
    new = seen = 0
    with db.connect() as conn:
        for url in feed_urls():
            root = fetch(url)
            time.sleep(DELAY)
            if root is None:
                continue
            for m in entries(root):
                seen += 1
                if collect.mentions_keyword(f"{m['title']} {m['body']}"):
                    new += db.upsert_mention(conn, m)
    print(f"Saw {seen} feed entries, {new} new mentions stored.")


if __name__ == "__main__":
    run()
