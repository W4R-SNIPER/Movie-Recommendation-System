"""Read movie recommendations from the precomputed SQLite index."""

import json
import sqlite3
import csv
import math
from bisect import bisect_left
from pathlib import Path

import numpy as np


DATABASE_PATH = Path(__file__).resolve().parent / "models" / "recommendations.sqlite"
DATASET_PATH = Path(__file__).resolve().parent / "data" / "clean_movies.csv"


class MovieRecommender:
    def __init__(self, path=DATABASE_PATH):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Recommendation database not found: {self.path}")
        with self._connect() as connection:
            connection.execute("SELECT 1 FROM movies LIMIT 1").fetchone()

    def _connect(self):
        return sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro", uri=True)

    def titles(self):
        with self._connect() as connection:
            return [row[0] for row in connection.execute(
                "SELECT DISTINCT title FROM movies ORDER BY title COLLATE NOCASE"
            )]

    def search_titles(self, query, limit=8):
        query = str(query).strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 12))
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._connect() as connection:
            prefix = [row[0] for row in connection.execute(
                "SELECT DISTINCT title FROM movies WHERE title LIKE ? ESCAPE '\\' "
                "ORDER BY title COLLATE NOCASE LIMIT ?",
                (escaped + "%", limit),
            )]
            if prefix:
                return prefix
            return [row[0] for row in connection.execute(
                "SELECT DISTINCT title FROM movies WHERE title LIKE ? ESCAPE '\\' "
                "ORDER BY title COLLATE NOCASE LIMIT ?",
                ("%" + escaped + "%", limit),
            )]

    def recommend(self, title, k=5, metric="cosine"):
        if metric != "cosine":
            raise ValueError("Only the precomputed cosine metric is available")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT movie_index, recommendations FROM movies "
                "WHERE title = ? COLLATE NOCASE ORDER BY movie_index LIMIT 1",
                (title.strip(),),
            ).fetchone()
            if row is None:
                raise KeyError(title)
            movie_index, raw_recommendations = row
            picks = json.loads(raw_recommendations)[:k]
            if not picks:
                return []
            placeholders = ",".join("?" for _ in picks)
            rows = connection.execute(
                f"SELECT movie_index, title, release_date, vote_average FROM movies "
                f"WHERE movie_index IN ({placeholders})",
                [pick[0] for pick in picks],
            ).fetchall()
        by_index = {movie[0]: movie for movie in rows}
        return [
            {"id": index, "name": by_index[index][1],
             "release_date": by_index[index][2], "rating": by_index[index][3],
             "similarity": round(float(score), 4)}
            for index, score in picks if index != movie_index and index in by_index
        ]


class GenreKNNRecommender:
    """K-nearest-neighbour recommendations over scaled rating and genre flags."""

    def __init__(self, path=DATASET_PATH):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"Movie dataset not found: {self.path}")

        self.movies = []
        all_genres = set()
        with self.path.open(newline="", encoding="utf-8-sig") as source:
            for row in csv.DictReader(source):
                try:
                    genres = json.loads(row.get("genres") or "[]")
                except (ValueError, TypeError):
                    genres = []
                if not isinstance(genres, list):
                    genres = []
                genres = sorted({str(value).strip() for value in genres if str(value).strip()})
                all_genres.update(genres)
                try:
                    rating = float(row.get("vote_average") or 0)
                except (TypeError, ValueError):
                    rating = 0.0
                self.movies.append({
                    "id": row.get("id", ""),
                    "name": (row.get("title") or "Untitled").strip() or "Untitled",
                    "rating": rating,
                    "genres": genres,
                })

        if not self.movies:
            raise ValueError(f"Movie dataset is empty: {self.path}")
        self.genres = sorted(all_genres, key=str.casefold)
        genre_indexes = {genre: i + 1 for i, genre in enumerate(self.genres)}
        self.matrix = np.zeros((len(self.movies), len(self.genres) + 1), dtype=np.float32)
        for row_index, movie in enumerate(self.movies):
            self.matrix[row_index, 0] = max(0.0, min(movie["rating"] / 10.0, 1.0))
            for genre in movie["genres"]:
                self.matrix[row_index, genre_indexes[genre]] = 1.0
        self.title_indexes = {}
        for index, movie in enumerate(self.movies):
            self.title_indexes.setdefault(movie["name"].casefold(), index)
        self.sorted_titles = sorted(
            ((movie["name"].casefold(), movie["name"]) for movie in self.movies),
            key=lambda item: item[0],
        )

    def titles(self):
        return sorted({movie["name"] for movie in self.movies}, key=str.casefold)

    def search_titles(self, query, limit=8):
        query = str(query).strip().casefold()
        if not query:
            return []
        limit = max(1, min(int(limit), 12))
        start = bisect_left(self.sorted_titles, (query, ""))
        matches = []
        for folded, title in self.sorted_titles[start:]:
            if not folded.startswith(query):
                break
            if not matches or title.casefold() != matches[-1].casefold():
                matches.append(title)
                if len(matches) == limit:
                    return matches
        if len(matches) < limit:
            for folded, title in self.sorted_titles:
                if query in folded and not any(title.casefold() == match.casefold() for match in matches):
                    matches.append(title)
                    if len(matches) == limit:
                        break
        return matches

    def _recommend(self, query, k, metric, exclude_index=None):
        if metric not in {"euclidean", "cosine"}:
            raise ValueError("metric must be 'euclidean' or 'cosine'")
        if not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer")

        if metric == "euclidean":
            distances = np.linalg.norm(self.matrix - query, axis=1)
        else:
            dots = self.matrix @ query
            norms = np.linalg.norm(self.matrix, axis=1) * np.linalg.norm(query)
            similarities = np.divide(dots, norms, out=np.zeros_like(dots), where=norms != 0)
            distances = 1.0 - similarities

        if exclude_index is not None:
            distances[exclude_index] = math.inf
        selected = np.argsort(distances, kind="stable")[:k]
        return [
            {**self.movies[index], "distance": round(float(distances[index]), 4)}
            for index in selected if math.isfinite(float(distances[index]))
        ]

    def recommend(self, title, k=5, metric="euclidean"):
        index = self.title_indexes.get(str(title).strip().casefold())
        if index is None:
            raise KeyError(title)
        return self._recommend(self.matrix[index].copy(), k, metric, exclude_index=index)

    def recommend_by_profile(self, rating, genres, k=5, metric="euclidean"):
        try:
            rating = float(rating)
        except (TypeError, ValueError) as error:
            raise ValueError("rating must be a number from 0 to 10") from error
        if not math.isfinite(rating) or not 0 <= rating <= 10:
            raise ValueError("rating must be from 0 to 10")

        selected_genres = {str(genre).strip().casefold() for genre in genres if str(genre).strip()}
        genre_lookup = {genre.casefold(): index + 1 for index, genre in enumerate(self.genres)}
        unknown = selected_genres - genre_lookup.keys()
        if unknown:
            raise ValueError(f"Unknown genre: {', '.join(sorted(unknown))}")

        query = np.zeros(self.matrix.shape[1], dtype=np.float32)
        query[0] = rating / 10.0
        for genre in selected_genres:
            query[genre_lookup[genre]] = 1.0
        return self._recommend(query, k, metric)
