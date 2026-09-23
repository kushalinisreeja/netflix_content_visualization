from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Netflix Content Dashboard", page_icon="🎬", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "netflix_cleaned.csv"
RED, DARK = "#E50914", "#221f1f"


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, parse_dates=["date_added"])


def top_n(series: pd.Series, n: int = 10, drop_unknown: bool = False) -> pd.DataFrame:
    """Split comma-separated values, count each item, return the top n."""
    items = series.dropna().str.split(",").explode().str.strip()
    items = items[items != ""]
    if drop_unknown:
        items = items[items != "Unknown"]
    counts = items.value_counts().head(n)
    return pd.DataFrame({"label": counts.index, "titles": counts.values})


df = load_data()

st.title("🎬 Netflix Content Dashboard")
st.caption("Explore what's on Netflix by type, year added, and rating.")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
all_types = sorted(df["type"].unique())
types = st.sidebar.multiselect("Type", all_types, default=all_types)

year_min, year_max = int(df["year_added"].min()), int(df["year_added"].max())
years = st.sidebar.slider("Year added", year_min, year_max, (year_min, year_max))

all_ratings = sorted(df["rating"].unique())
ratings = st.sidebar.multiselect("Rating", all_ratings, default=all_ratings)

# ---------- Apply filters ----------
filtered = df[df["type"].isin(types) & df["year_added"].between(years[0], years[1])]
if ratings:
    filtered = filtered[filtered["rating"].isin(ratings)]

if filtered.empty:
    st.warning("No titles match these filters. Try widening them.")
    st.stop()

# ---------- KPIs ----------
c1, c2, c3 = st.columns(3)
c1.metric("Total titles", f"{len(filtered):,}")
c2.metric("Movies", f"{(filtered['type'] == 'Movie').sum():,}")
c3.metric("TV shows", f"{(filtered['type'] == 'TV Show').sum():,}")

st.divider()

# ---------- Charts ----------
left, right = st.columns(2)

yearly = filtered.groupby(["year_added", "type"]).size().reset_index(name="titles")
fig_year = px.bar(
    yearly, x="year_added", y="titles", color="type",
    color_discrete_map={"Movie": RED, "TV Show": DARK},
    title="Titles added per year",
)
left.plotly_chart(fig_year, use_container_width=True)

rating_counts = filtered["rating"].value_counts().reset_index()
rating_counts.columns = ["rating", "titles"]
fig_rating = px.bar(
    rating_counts, x="rating", y="titles",
    color_discrete_sequence=[RED], title="Rating distribution",
)
right.plotly_chart(fig_rating, use_container_width=True)

left2, right2 = st.columns(2)

countries = top_n(filtered["country"], drop_unknown=True).sort_values("titles")
fig_country = px.bar(
    countries, x="titles", y="label", orientation="h",
    color_discrete_sequence=[RED], title="Top 10 countries",
)
left2.plotly_chart(fig_country, use_container_width=True)

genres = top_n(filtered["listed_in"]).sort_values("titles")
fig_genre = px.bar(
    genres, x="titles", y="label", orientation="h",
    color_discrete_sequence=[RED], title="Top 10 genres",
)
right2.plotly_chart(fig_genre, use_container_width=True)

# ---------- Raw table ----------
with st.expander("View filtered data"):
    st.dataframe(
        filtered[["title", "type", "country", "release_year", "year_added", "rating", "listed_in"]]
    )