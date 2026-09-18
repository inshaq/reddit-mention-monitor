"""Classify unanalyzed mentions with Claude."""
import json
import re
import time

import anthropic

import config
import db

TOPICS = ["pricing", "model_selection", "latency", "reliability", "concurrency_limits", "context_limits",
          "docs", "support", "ux", "quality", "comparison", "other"]

PROMPT = """You analyze Reddit content for {brand}, {brand_description}.

Subreddit: r/{subreddit}
Thread title: {title}
Kind: {kind}
Text:
\"\"\"
{body}
\"\"\"

Return ONLY a JSON object with these keys:
- "relevant": true only if the text is genuinely about {brand} the company/product \
(false when the keyword is just an ordinary word used in an unrelated sense)
- "sentiment": "positive" | "negative" | "neutral" | "mixed" (toward {brand}; "neutral" if not relevant)
- "topics": list drawn from {topics}
- "feedback_type": "praise" | "complaint" | "feature_request" | "question" | "comparison" | "none"
- "summary": one sentence stating what the person actually thinks or asks, in plain words
- "actionable": true if the company could act on it (a concrete complaint, bug, missing feature, \
or pricing/limit friction)"""


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON in response: {text[:200]}")
    return json.loads(match.group(0))


def normalize(a: dict) -> dict:
    return {
        "relevant": bool(a.get("relevant")),
        "sentiment": a.get("sentiment", "neutral"),
        "topics": [t for t in a.get("topics", []) if t in TOPICS],
        "feedback_type": a.get("feedback_type", "none"),
        "summary": a.get("summary", ""),
        "actionable": bool(a.get("actionable")),
    }


def run(limit: int = 500):
    client = anthropic.Anthropic()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM mentions WHERE analyzed_at IS NULL ORDER BY created_utc DESC LIMIT ?",
            (limit,),
        ).fetchall()
        done = failed = 0
        for r in rows:
            try:
                resp = client.messages.create(
                    model=config.MODEL,
                    max_tokens=400,
                    messages=[{"role": "user", "content": PROMPT.format(
                        brand=config.BRAND_NAME, brand_description=config.BRAND_DESCRIPTION, subreddit=r["subreddit"], title=r["title"], kind=r["kind"],
                        body=(r["body"] or "")[:4000], topics=TOPICS)}],
                )
                db.save_analysis(conn, r["id"], normalize(parse_json(resp.content[0].text)), time.time())
                conn.commit()
                done += 1
            except Exception as e:  # leave the row unanalyzed so the next run retries it
                failed += 1
                print(f"  skipped {r['id']}: {e}")
        print(f"Analyzed {done}, failed {failed}.")


if __name__ == "__main__":
    run()
