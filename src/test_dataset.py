"""Integrity checks for the single consolidated movie dataset."""

import json
import sqlite3
from pathlib import Path

import pandas as pd


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "clean_movies.csv"
INDEX_PATH = Path(__file__).resolve().parents[1] / "models" / "recommendations.sqlite"


def test_clean_dataset_has_unique_movie_ids_and_titles():
    movies = pd.read_csv(DATASET_PATH, low_memory=False)
    assert movies["id"].notna().all()
    assert movies["id"].is_unique
    assert movies["title"].notna().all()
    assert movies["title"].astype(str).str.strip().ne("").all()


def test_structured_movie_fields_are_json_arrays():
    movies = pd.read_csv(
        DATASET_PATH,
        usecols=["genres", "keywords", "cast", "director"],
        low_memory=False,
    )
    for column in movies.columns:
        assert all(
            isinstance(json.loads(value), list)
            for value in movies[column].fillna("[]")
        )


def test_dataset_order_matches_recommendation_index():
    titles = pd.read_csv(DATASET_PATH, usecols=["title"], low_memory=False)["title"]
    with sqlite3.connect(f"file:{INDEX_PATH.as_posix()}?mode=ro", uri=True) as db:
        indexed_titles = [
            row[0] for row in db.execute(
                "SELECT title FROM movies ORDER BY movie_index"
            )
        ]
    assert titles.fillna("Untitled").astype(str).tolist() == indexed_titles
