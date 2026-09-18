import json
import sqlite3
from contextlib import contextmanager

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS mentions (
    id TEXT PRIMARY KEY,           -- reddit fullname, e.g. t3_abc / t1_xyz
    kind TEXT NOT NULL,            -- post | comment
    subreddit TEXT,
    title TEXT,
    body TEXT,
    url TEXT,
    score INTEGER,
    created_utc REAL,
    -- analysis (NULL until analyzed)
    relevant INTEGER,
    sentiment TEXT,
    topics TEXT,                   -- JSON list
    feedback_type TEXT,
    summary TEXT,
    actionable INTEGER,
    analyzed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_created ON mentions(created_utc);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_mention(conn, m: dict) -> bool:
    """Insert a new mention; refresh score on existing ones. Returns True if new."""
    row = conn.execute("SELECT 1 FROM mentions WHERE id = ?", (m["id"],)).fetchone()
    if row:
        conn.execute("UPDATE mentions SET score = ? WHERE id = ?", (m["score"], m["id"]))
        return False
    conn.execute(
        """INSERT INTO mentions (id, kind, subreddit, title, body, url, score, created_utc)
           VALUES (:id, :kind, :subreddit, :title, :body, :url, :score, :created_utc)""",
        m,
    )
    return True


def save_analysis(conn, mention_id: str, a: dict, now: float):
    conn.execute(
        """UPDATE mentions SET relevant=?, sentiment=?, topics=?, feedback_type=?,
           summary=?, actionable=?, analyzed_at=? WHERE id=?""",
        (
            int(a["relevant"]),
            a["sentiment"],
            json.dumps(a["topics"]),
            a["feedback_type"],
            a["summary"],
            int(a["actionable"]),
            now,
            mention_id,
        ),
    )
