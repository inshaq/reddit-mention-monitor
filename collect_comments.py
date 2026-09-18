"""Keyless comment poller: each subreddit's newest-comments RSS feed.

Catches brand mentions inside threads whose post never mentions the brand. Reddit only serves
the latest ~25 comments per subreddit, so run this often (e.g. every 10-15 minutes) on busy
subreddits; anything that scrolls past between runs is missed. Authors are never stored.

    python collect_comments.py             # one pass
    python collect_comments.py --every 600 # loop, one pass every 10 minutes
"""
import argparse
import re
import time

import collect
import collect_rss as rss
import config
import db


def comment_rows(root):
    for e in root.findall("a:entry", rss.NS):
        cid = e.findtext("a:id", "", rss.NS)  # e.g. t1_pam0cbp
        link = e.find("a:link", rss.NS).get("href")
        cat = e.find("a:category", rss.NS)
        # Feed titles look like "/u/<author> on <thread title>"; keep only the thread title.
        thread = re.sub(r"^/u/\S+ on ", "", e.findtext("a:title", "", rss.NS))
        yield {
            "id": cid,
            "kind": "comment",
            "subreddit": cat.get("term") if cat is not None else "",
            "title": thread,
            "body": rss.strip_html(e.findtext("a:content", "", rss.NS)),
            "url": link,
            "score": 0,  # RSS doesn't expose score
            "created_utc": rss.datetime.fromisoformat(e.findtext("a:updated", "", rss.NS)).timestamp(),
        }


def run_once():
    seen = new = 0
    with db.connect() as conn:
        for sub in config.SUBREDDITS:
            root = rss.fetch(f"https://www.reddit.com/r/{sub}/comments.rss")
            time.sleep(rss.DELAY)
            if root is None:
                continue
            for m in comment_rows(root):
                seen += 1
                if collect.mentions_keyword(m["body"]):
                    new += db.upsert_mention(conn, m)
    print(f"{time.strftime('%H:%M')} saw {seen} comments across {len(config.SUBREDDITS)} subreddits, {new} new mentions.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, metavar="SECONDS", help="loop forever, one pass per interval")
    args = ap.parse_args()
    run_once()
    while args.every:
        time.sleep(args.every)
        run_once()
