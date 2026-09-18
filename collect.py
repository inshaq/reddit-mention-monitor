"""Pull brand mentions from Reddit into SQLite."""
import os

import praw

import config
import db


def reddit_client() -> praw.Reddit:
    cid, secret = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        raise SystemExit("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env (see .env.example)")
    return praw.Reddit(
        client_id=cid,
        client_secret=secret,
        user_agent=os.getenv("REDDIT_USER_AGENT", "reddit-mention-monitor/0.1"),
    )


def mentions_keyword(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in config.KEYWORDS)


def post_row(p) -> dict:
    return {
        "id": p.fullname,
        "kind": "post",
        "subreddit": p.subreddit.display_name,
        "title": p.title,
        "body": p.selftext or "",
        "url": f"https://www.reddit.com{p.permalink}",
        "score": p.score,
        "created_utc": p.created_utc,
    }


def comment_row(c, post) -> dict:
    return {
        "id": c.fullname,
        "kind": "comment",
        "subreddit": post.subreddit.display_name,
        "title": post.title,
        "body": c.body,
        "url": f"https://www.reddit.com{c.permalink}",
        "score": c.score,
        "created_utc": c.created_utc,
    }


def run():
    reddit = reddit_client()
    seen_posts = {}

    searches = [(reddit.subreddit("all"), q) for q in config.SEARCH_QUERIES]
    searches += [(reddit.subreddit(s), config.PRIMARY_TERM) for s in config.SUBREDDITS]
    for target, query in searches:
        for p in target.search(query, sort="new", time_filter="year", limit=config.SEARCH_LIMIT):
            seen_posts[p.fullname] = p

    new = 0
    with db.connect() as conn:
        for p in seen_posts.values():
            # A search hit isn't always about us (the word is generic), so require the keyword
            # in the post itself, otherwise only keep comments that mention it.
            if mentions_keyword(f"{p.title} {p.selftext}"):
                new += db.upsert_mention(conn, post_row(p))
            p.comment_limit = config.MAX_COMMENTS_PER_POST
            p.comments.replace_more(limit=0)
            for c in p.comments.list():
                if mentions_keyword(c.body):
                    new += db.upsert_mention(conn, comment_row(c, p))
    print(f"Scanned {len(seen_posts)} posts, {new} new mentions stored.")


if __name__ == "__main__":
    run()
