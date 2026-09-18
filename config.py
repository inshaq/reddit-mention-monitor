import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "mentions.db")
MODEL = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")

# The brand/product being monitored, set in .env (see .env.example).
BRAND_NAME = os.getenv("BRAND_NAME", "Brand")
BRAND_DESCRIPTION = os.getenv("BRAND_DESCRIPTION", "a product")

# Phrases that count as a mention, most specific first. Comments are kept only if they contain one.
KEYWORDS = [k.strip().lower() for k in os.getenv("BRAND_KEYWORDS", "").split(",") if k.strip()]
if not KEYWORDS:
    raise SystemExit("Set BRAND_KEYWORDS in .env (comma-separated, most specific first)")

# Broadest term, used for per-subreddit searches
PRIMARY_TERM = KEYWORDS[-1]

# Reddit-wide search queries: multi-word or dotted phrases are quoted for exact match
SEARCH_QUERIES = [f'"{k}"' if (" " in k or "." in k) else k for k in KEYWORDS]

# Extra subreddits searched individually, since they surface mentions site-wide search misses
SUBREDDITS = ["LocalLLaMA", "SillyTavernAI", "JanitorAI_Official", "ChatGPTCoding", "LLMDevs"]

SEARCH_LIMIT = 100
MAX_COMMENTS_PER_POST = 200
