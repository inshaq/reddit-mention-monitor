"""Fill the DB with clearly fake sample mentions so the dashboard can be tried without API keys."""
import json
import time

import db

DAY = 86400
now = time.time()

# (subreddit, kind, text summary, sentiment, topics, feedback_type, actionable, score, days_ago)
SAMPLES = [
    ("LocalLLaMA", "comment", "Love that I can swap between hundreds of models without managing GPUs.", "positive", ["model_selection"], "praise", False, 42, 2),
    ("SillyTavernAI", "comment", "Flat pricing is way better than per-token for long roleplay sessions.", "positive", ["pricing"], "praise", False, 31, 3),
    ("SillyTavernAI", "post", "Concurrency limit on my plan is too low, can't run two chats at once.", "negative", ["concurrency_limits", "pricing"], "complaint", True, 27, 4),
    ("LocalLLaMA", "comment", "Latency on the bigger models is noticeably slow at peak hours.", "negative", ["latency", "reliability"], "complaint", True, 18, 5),
    ("JanitorAI_Official", "comment", "Would be great to have a cheaper tier for casual use.", "neutral", ["pricing"], "feature_request", True, 12, 6),
    ("LLMDevs", "post", "How does this compare with OpenRouter for open-weight models?", "neutral", ["comparison"], "question", False, 9, 7),
    ("LocalLLaMA", "comment", "New model support is added fast, day-one for most releases.", "positive", ["model_selection", "quality"], "praise", False, 25, 9),
    ("SillyTavernAI", "comment", "Docs for the API are thin, had to guess the context length settings.", "negative", ["docs"], "complaint", True, 8, 11),
    ("ChatGPTCoding", "comment", "Works fine but the tool-calling support on some models is flaky.", "mixed", ["quality", "reliability"], "complaint", True, 6, 14),
    ("LocalLLaMA", "comment", "Support replied within a day and fixed my billing issue.", "positive", ["support"], "praise", False, 15, 18),
]

with db.connect() as conn:
    for i, (sub, kind, text, sent, topics, ftype, act, score, ago) in enumerate(SAMPLES):
        m = {
            "id": f"sample_{i}", "kind": kind, "subreddit": sub, "title": "[SAMPLE DATA]",
            "body": text, "url": "https://www.reddit.com/r/" + sub, "score": score,
            "created_utc": now - ago * DAY,
        }
        db.upsert_mention(conn, m)
        db.save_analysis(conn, m["id"], {
            "relevant": True, "sentiment": sent, "topics": topics,
            "feedback_type": ftype, "summary": text, "actionable": act,
        }, now)
print(f"Seeded {len(SAMPLES)} sample mentions.")
