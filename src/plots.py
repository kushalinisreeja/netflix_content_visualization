"""Plotting functions for the Netflix visualization notebook.

Every function takes the cleaned dataframe, saves a PNG to images/ (unless
save=False) and shows the chart.

Run the whole pipeline (load/clean if needed, then draw every chart) with:
    python -m src.plots
"""
import calendar
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from clean import explode_column

RED, DARK = "#E50914", "#221f1f"
IMAGES_DIR = Path(__file__).resolve().parents[1] / "images"

sns.set_theme(style="whitegrid")


def save_fig(name: str) -> None:
    """Save the current figure to images/<name>.png."""
    IMAGES_DIR.mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / f"{name}.png", dpi=150, bbox_inches="tight")


def _finish(name: str, save: bool) -> None:
    if save:
        save_fig(name)
    plt.show()


def plot_type_split(df, save=True):
    counts = df["type"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    _, _, autotexts = ax.pie(
        counts, labels=counts.index, autopct="%1.1f%%", startangle=90,
        colors=[RED, DARK], wedgeprops=dict(width=0.4),
    )
    for t in autotexts:
        t.set_color("white")
    ax.set_title("Content split: Movies vs TV Shows")
    _finish("01_type_split", save)


def plot_titles_per_year(df, save=True):
    yearly = df.groupby(["year_added", "type"]).size().unstack(fill_value=0)
    ax = yearly.plot(kind="line", marker="o", figsize=(10, 5), color=[RED, DARK])
    ax.set_title("Titles added to Netflix per year")
    ax.set_xlabel("Year added")
    ax.set_ylabel("Number of titles")
    _finish("02_titles_per_year", save)


def plot_titles_per_month(df, save=True):
    month_order = list(calendar.month_name)[1:]
    monthly = df["month_name"].value_counts().reindex(month_order, fill_value=0)
    plt.figure(figsize=(10, 5))
    sns.barplot(x=monthly.index, y=monthly.values, color=RED)
    plt.xticks(rotation=45)
    plt.title("Titles added by month")
    plt.xlabel("")
    plt.ylabel("Number of titles")
    _finish("03_titles_per_month", save)


def plot_top_countries(df, n=10, save=True):
    top = explode_column(df, "country", drop_unknown=True).value_counts().head(n)
    plt.figure(figsize=(9, 5))
    sns.barplot(x=top.values, y=top.index, color=RED)
    plt.title(f"Top {n} content-producing countries")
    plt.xlabel("Number of titles")
    plt.ylabel("")
    _finish("04_top_countries", save)


def plot_top_genres(df, n=10, save=True):
    top = explode_column(df, "listed_in").value_counts().head(n)
    plt.figure(figsize=(9, 5))
    sns.barplot(x=top.values, y=top.index, color=RED)
    plt.title(f"Top {n} genres")
    plt.xlabel("Number of titles")
    plt.ylabel("")
    _finish("05_top_genres", save)


def plot_ratings(df, save=True):
    order = df["rating"].value_counts().index
    plt.figure(figsize=(9, 6))
    sns.countplot(data=df, y="rating", order=order, color=RED)
    plt.title("Content by maturity rating")
    plt.xlabel("Number of titles")
    plt.ylabel("")
    _finish("06_ratings", save)


def plot_movie_duration(df, save=True):
    movies = df[df["type"] == "Movie"].dropna(subset=["duration_min"])
    plt.figure(figsize=(9, 5))
    sns.histplot(movies["duration_min"], bins=30, kde=True, color=RED)
    plt.title("Movie duration distribution")
    plt.xlabel("Duration (minutes)")
    _finish("07_movie_duration", save)
    print("Median movie length:", movies["duration_min"].median(), "minutes")


def plot_tv_seasons(df, save=True):
    tv = df[df["type"] == "TV Show"].dropna(subset=["seasons"]).copy()
    tv["seasons"] = tv["seasons"].astype(int)
    plt.figure(figsize=(9, 5))
    sns.countplot(data=tv, x="seasons", color=DARK)
    plt.title("Number of seasons per TV show")
    plt.xlabel("Seasons")
    plt.ylabel("Number of shows")
    _finish("08_tv_seasons", save)


def plot_release_lag(df, cap=20, save=True):
    lag = df["year_added"] - df["release_year"]
    lag = lag[lag >= 0].clip(upper=cap)  # drop negatives; group anything older than cap
    plt.figure(figsize=(9, 5))
    sns.histplot(lag, discrete=True, color=RED)  # one bar per whole year
    plt.title(f"Years between release and being added to Netflix (capped at {cap})")
    plt.xlabel("Years")
    plt.ylabel("Number of titles")
    _finish("09_release_lag", save)


def plot_wordcloud(df, save=True):
    from wordcloud import STOPWORDS, WordCloud  # imported here so other plots work without it

    text = " ".join(df["description"].dropna())
    wc = WordCloud(
        width=1000, height=500, background_color="white",
        stopwords=STOPWORDS, colormap="Reds",
    ).generate(text)
    plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title("Most common words in descriptions")
    _finish("10_wordcloud", save)


def plot_world_map(df, save=True):
    import plotly.express as px  # imported here so matplotlib plots work without it

    counts = explode_column(df, "country", drop_unknown=True).value_counts().reset_index()
    counts.columns = ["country", "titles"]
    fig = px.choropleth(
        counts, locations="country", locationmode="country names",
        color="titles", color_continuous_scale="Reds",
        title="Netflix titles by country",
    )
    if save:
        IMAGES_DIR.mkdir(exist_ok=True)
        fig.write_html(IMAGES_DIR / "11_world_map.html")
    fig.show()


def plot_all(df, save=True):
    """Draw every chart in order."""
    plot_type_split(df, save)
    plot_titles_per_year(df, save)
    plot_titles_per_month(df, save)
    plot_top_countries(df, save=save)
    plot_top_genres(df, save=save)
    plot_ratings(df, save)
    plot_movie_duration(df, save)
    plot_tv_seasons(df, save)
    plot_release_lag(df, save=save)
    plot_wordcloud(df, save)
    plot_world_map(df, save)


if __name__ == "__main__":
    from clean import PROCESSED_PATH, clean_netflix, load_processed, load_raw, save_processed

    if PROCESSED_PATH.exists():
        df = load_processed()
    else:
        df = clean_netflix(load_raw())
        save_processed(df)

    plot_all(df)