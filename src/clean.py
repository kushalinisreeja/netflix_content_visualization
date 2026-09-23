"""Cleaning functions for the Netflix titles dataset.

Run the whole pipeline from the project root with:
    python -m src.clean
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "netflix_titles.csv"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "netflix_cleaned.csv"


def load_raw(path=RAW_PATH) -> pd.DataFrame:
    """Read the raw Netflix CSV."""
    return pd.read_csv(path)


def clean_netflix(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the raw Netflix dataframe."""
    df = df.drop_duplicates().copy()

    # 1. A few rows have the runtime typed into `rating`: move it back FIRST,
    #    so the duration split below sees the right values.
    mask = df["rating"].str.contains("min", na=False)
    df.loc[mask, "duration"] = df.loc[mask, "rating"]
    df.loc[mask, "rating"] = "Unknown"

    # 2. Missing text values: label them instead of dropping rows.
    for col in ["director", "cast", "country", "rating"]:
        df[col] = df[col].fillna("Unknown")

    # 3. Dates: strip spaces, parse, drop the few rows without a date.
    df["date_added"] = pd.to_datetime(df["date_added"].str.strip(), errors="coerce")
    df = df.dropna(subset=["date_added"]).copy()
    df["year_added"] = df["date_added"].dt.year.astype(int)
    df["month_added"] = df["date_added"].dt.month.astype(int)
    df["month_name"] = df["date_added"].dt.month_name()

    # 4. Duration: "90 min" -> 90 (movies), "2 Seasons" -> 2 (TV shows).
    #    NaN here means "not applicable" (a movie has no seasons), so leave it.
    df["duration_value"] = pd.to_numeric(df["duration"].str.extract(r"(\d+)")[0])
    df["duration_min"] = df["duration_value"].where(df["type"] == "Movie")
    df["seasons"] = df["duration_value"].where(df["type"] == "TV Show")

    # 5. Simple "main" value for multi-value columns.
    df["primary_country"] = df["country"].str.split(",").str[0].str.strip()
    df["primary_genre"] = df["listed_in"].str.split(",").str[0].str.strip()

    return df


def explode_column(df: pd.DataFrame, column: str, drop_unknown: bool = False) -> pd.Series:
    """Split a comma-separated column into one item per row (for counting)."""
    items = df[column].str.split(",").explode().str.strip()
    items = items[items != ""]
    if drop_unknown:
        items = items[items != "Unknown"]
    return items


def save_processed(df: pd.DataFrame, path=PROCESSED_PATH) -> None:
    """Write the cleaned dataframe to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_processed(path=PROCESSED_PATH) -> pd.DataFrame:
    """Read the cleaned CSV with dates parsed."""
    return pd.read_csv(path, parse_dates=["date_added"])


if __name__ == "__main__":
    raw = load_raw()
    cleaned = clean_netflix(raw)
    save_processed(cleaned)
    print(f"Raw: {raw.shape} -> Cleaned: {cleaned.shape}")
    print(f"Saved to {PROCESSED_PATH}")