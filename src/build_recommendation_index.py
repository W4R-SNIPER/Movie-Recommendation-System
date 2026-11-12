"""Build the small, queryable movie catalog used by the Flask app.

Run from the project root with:
    python src/build_recommendation_index.py

This offline step reads the full CSV and TF-IDF matrix once. The website then
uses SQLite to fetch only titles, the selected movie, and its five picks.
"""

import json
import os
import pickle
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MOVIES_PATH = ROOT / "data" / "clean_movies.csv"
MATRIX_PATH = ROOT / "models" / "tfidf_matrix.pkl"
OUTPUT_PATH = ROOT / "models" / "recommendations.sqlite"
TEMP_PATH = OUTPUT_PATH.with_suffix(".sqlite.tmp")
TOP_K = 5
BATCH_SIZE = 64


def top_recommendations(movie_count, movie_index, scores, indices):
    non_self = indices != movie_index
    indices = indices[non_self]
    scores = scores[non_self]

    if len(indices) >= TOP_K:
        selected = np.argpartition(scores, -TOP_K)[-TOP_K:]
        indices = indices[selected]
        scores = scores[selected]
    else:
        # Match the old zero-score tie behavior by filling from the catalog end.
        used = set(indices.tolist())
        used.add(movie_index)
        extra_indices = []
        for candidate in range(movie_count - 1, -1, -1):
            if candidate not in used:
                extra_indices.append(candidate)
                if len(indices) + len(extra_indices) == TOP_K:
                    break
        if extra_indices:
            indices = np.concatenate((indices, np.asarray(extra_indices, dtype=np.int64)))
            scores = np.concatenate((scores, np.zeros(len(extra_indices), dtype=scores.dtype)))

    order = np.argsort(scores)[::-1]
    return [[int(indices[i]), float(scores[i])] for i in order[:TOP_K]]


def main():
    movies = pd.read_csv(
        MOVIES_PATH,
        usecols=["title", "release_date", "vote_average"],
    )
    movies["title"] = movies["title"].fillna("Untitled").astype(str)

    with MATRIX_PATH.open("rb") as file:
        matrix = pickle.load(file).tocsr().astype(np.float32)
    matrix.sort_indices()

    if matrix.shape[0] != len(movies):
        raise ValueError(
            f"Movie/model row mismatch: {len(movies)} movies, {matrix.shape[0]} model rows"
        )

    TEMP_PATH.unlink(missing_ok=True)
    connection = sqlite3.connect(TEMP_PATH)
    connection.executescript("""
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        PRAGMA temp_store=MEMORY;
        CREATE TABLE movies (
            movie_index INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_date TEXT,
            vote_average REAL,
            recommendations TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX title_index ON movies(title COLLATE NOCASE);
    """)

    records = []
    for row in movies.itertuples(index=False, name=None):
        title, release_date, vote_average = row
        records.append((
            str(title),
            None if pd.isna(release_date) else str(release_date),
            None if pd.isna(vote_average) else float(vote_average),
        ))
    connection.executemany(
        "INSERT INTO movies(movie_index, title, release_date, vote_average) VALUES (?, ?, ?, ?)",
        ((i, *record) for i, record in enumerate(records)),
    )

    matrix_transpose = matrix.T.tocsr()
    for start in range(0, matrix.shape[0], BATCH_SIZE):
        stop = min(start + BATCH_SIZE, matrix.shape[0])
        similarities = (matrix[start:stop] @ matrix_transpose).tocsr()
        updates = []
        for offset, movie_index in enumerate(range(start, stop)):
            row_start, row_stop = similarities.indptr[offset:offset + 2]
            indices = similarities.indices[row_start:row_stop]
            scores = similarities.data[row_start:row_stop]
            picks = top_recommendations(
                matrix.shape[0], movie_index, scores, indices
            )
            updates.append((json.dumps(picks, separators=(",", ":")), movie_index))
        connection.executemany(
            "UPDATE movies SET recommendations = ? WHERE movie_index = ?",
            updates,
        )
        if stop % 2048 == 0 or stop == matrix.shape[0]:
            print(f"Indexed {stop:,}/{matrix.shape[0]:,} movies", flush=True)

    connection.commit()
    connection.close()
    os.replace(TEMP_PATH, OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
