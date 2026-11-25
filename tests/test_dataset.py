"""Check the dataset required by the KNN app."""
import csv
import json
from pathlib import Path


def test_dataset_has_unique_ids_titles_and_valid_genres():
    path = Path(__file__).resolve().parents[1] / "data" / "clean_movies.csv"
    with path.open(newline="", encoding="utf-8-sig") as source:
        movies = list(csv.DictReader(source))
    assert movies
    ids = [movie["id"] for movie in movies]
    assert all(ids)
    assert len(ids) == len(set(ids))
    assert all(movie["title"].strip() for movie in movies)
    assert all(isinstance(json.loads(movie["genres"] or "[]"), list) for movie in movies)
