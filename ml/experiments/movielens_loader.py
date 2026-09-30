"""Load raw MovieLens 32M CSVs into pandas DataFrames.

Expects data/raw/ml-32m/ to contain links.csv, movies.csv, ratings.csv,
and tags.csv (from https://files.grouplens.org/datasets/movielens/ml-32m.zip).
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ml-32m"


def load_ratings() -> pd.DataFrame:
    """userId, movieId, rating (0.5-5.0 stars), timestamp (unix seconds)."""
    df = pd.read_csv(DATA_DIR / "ratings.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def load_movies() -> pd.DataFrame:
    """movieId, title, genres (pipe-separated, e.g. 'Action|Sci-Fi')."""
    df = pd.read_csv(DATA_DIR / "movies.csv")
    df["genres"] = df["genres"].str.split("|")
    return df


def load_links() -> pd.DataFrame:
    """movieId, imdbId, tmdbId — maps MovieLens ids to TMDB/IMDb ids."""
    return pd.read_csv(DATA_DIR / "links.csv")


def load_tags() -> pd.DataFrame:
    """userId, movieId, tag (free-text), timestamp."""
    df = pd.read_csv(DATA_DIR / "tags.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def load_all() -> dict[str, pd.DataFrame]:
    """Convenience: load everything at once for notebook use."""
    return {
        "ratings": load_ratings(),
        "movies": load_movies(),
        "links": load_links(),
        "tags": load_tags(),
    }


if __name__ == "__main__":
    data = load_all()
    for name, df in data.items():
        print(f"{name}: {len(df):,} rows, columns={list(df.columns)}")
