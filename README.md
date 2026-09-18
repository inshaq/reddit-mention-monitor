# Reddit Mention Monitor

Personal side project: collect Reddit mentions of a configurable product/brand, classify sentiment and
feedback with Claude, and browse them in a Streamlit dashboard.

## Setup
    python3 -m venv .venv && .venv/bin/pip install praw anthropic streamlit pandas plotly python-dotenv
    cp .env.example .env   # fill in Reddit + Anthropic keys and the brand to monitor

## Run
    .venv/bin/python collect.py      # fetch mentions from Reddit
    .venv/bin/python analyze.py      # classify new mentions with Claude
    .venv/bin/streamlit run dashboard.py

No keys yet? `.venv/bin/python seed_sample.py` loads fake data so the dashboard works.

## Data and API use
- **Read-only.** The tool only searches and reads public posts and comments. It never posts,
  comments, votes, messages, or moderates.
- **Scope.** A small set of subreddits (see `config.py`) and a few search queries, at low volume
  (a few hundred requests per day at most).
- **Storage.** Public post/comment text and permalinks are stored in a local SQLite file.
  Usernames are not stored. The database and credentials are gitignored and never published.
- **Use of data.** Text is sent to an LLM only to classify sentiment and topics. It is not used
  to train models, resold, or shared, and nothing is inferred about individual users.
- **Credentials.** A Reddit "script" app on the developer's own account, read via environment variables.
