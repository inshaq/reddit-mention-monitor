import json

import pandas as pd
import plotly.express as px
import streamlit as st

import config
import db

st.set_page_config(page_title=f"{config.BRAND_NAME} on Reddit", layout="wide")
st.title(f"{config.BRAND_NAME} on Reddit")

SENT_COLORS = {"positive": "#2e9e6b", "negative": "#d9534f", "mixed": "#e0a030", "neutral": "#8a8f98"}


@st.cache_data(ttl=60)
def load() -> pd.DataFrame:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM mentions WHERE relevant = 1").fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["created_utc"], unit="s")
    df["topics"] = df["topics"].apply(lambda t: json.loads(t) if t else [])
    return df


df = load()
if df.empty:
    st.info("No analyzed mentions yet. Run `python collect.py` then `python analyze.py`, "
            "or `python seed_sample.py` for sample data.")
    st.stop()

if df["title"].eq("[SAMPLE DATA]").any():
    st.warning("Showing sample data, not real Reddit mentions.")

days = st.sidebar.selectbox("Time range", [7, 30, 90, 365], index=1, format_func=lambda d: f"Last {d} days")
subs = st.sidebar.multiselect("Subreddits", sorted(df["subreddit"].unique()))
df = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=days)]
if subs:
    df = df[df["subreddit"].isin(subs)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Mentions", len(df))
c2.metric("Positive", f"{(df['sentiment'] == 'positive').mean():.0%}" if len(df) else "–")
c3.metric("Negative", f"{(df['sentiment'] == 'negative').mean():.0%}" if len(df) else "–")
c4.metric("Actionable", int(df["actionable"].sum()))

left, right = st.columns(2)
with left:
    st.subheader("Sentiment over time")
    weekly = df.set_index("date").groupby([pd.Grouper(freq="W"), "sentiment"]).size().reset_index(name="n")
    st.plotly_chart(px.bar(weekly, x="date", y="n", color="sentiment", color_discrete_map=SENT_COLORS),
                    width="stretch")
with right:
    st.subheader("Topics by sentiment")
    exploded = df.explode("topics").dropna(subset=["topics"])
    by_topic = exploded.groupby(["topics", "sentiment"]).size().reset_index(name="n")
    st.plotly_chart(px.bar(by_topic, x="n", y="topics", color="sentiment", orientation="h",
                           color_discrete_map=SENT_COLORS), width="stretch")


def show(frame: pd.DataFrame):
    for _, r in frame.sort_values(["score", "date"], ascending=False).iterrows():
        st.markdown(f"**{r['summary']}**  \n"
                    f"r/{r['subreddit']} · {r['kind']} · {r['date']:%b %d} · "
                    f"{', '.join(r['topics'])} · [link]({r['url']})"
                    + (f"  \nin thread: _{r['title']}_" if r["kind"] == "comment" else ""))


tab_fix, tab_love, tab_all = st.tabs(["What to improve", "What people like", "All mentions"])
with tab_fix:
    show(df[(df["actionable"] == 1) | (df["sentiment"] == "negative")])
with tab_love:
    show(df[df["sentiment"] == "positive"])
with tab_all:
    st.dataframe(df[["date", "subreddit", "kind", "sentiment", "feedback_type", "summary", "score", "url"]]
                 .sort_values("date", ascending=False), width="stretch", hide_index=True)
