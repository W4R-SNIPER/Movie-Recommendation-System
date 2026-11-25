from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import pandas as pd
import pickle

from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches


print("Loading movies...")

movies = pd.read_csv(ROOT / "data" / 'clean_movies.csv')

print("Loading TF-IDF matrix...")

with open(ROOT / "models" / 'tfidf_matrix.pkl', "rb") as file:
    tfidf_matrix = pickle.load(file)


def normalize_title(title):
    return " ".join(
        str(title).lower().strip().split()
    )


movies["search_title"] = movies["title"].apply(
    normalize_title
)


def find_movie(query):

    query = normalize_title(query)

    # Exact match
    exact_matches = movies[
        movies["search_title"] == query
    ]

    if len(exact_matches) > 0:

        if len(exact_matches) == 1:
            return exact_matches.index[0]

        print("\nMultiple movies found:")

        for i, index in enumerate(
            exact_matches.index[:10],
            1
        ):
            print(
                f"{i}. {movies.loc[index, 'title']}"
            )

        choice = input(
            "\nEnter movie number: "
        ).strip()

        if choice.isdigit():

            choice = int(choice)

            if 1 <= choice <= min(
                10,
                len(exact_matches)
            ):
                return exact_matches.index[
                    choice - 1
                ]

        return None

    # Partial match
    partial_matches = movies[
        movies["search_title"].str.contains(
            query,
            case=False,
            na=False
        )
    ]

    if len(partial_matches) > 0:

        print("\nMovies matching your search:")

        for i, index in enumerate(
            partial_matches.index[:10],
            1
        ):
            print(
                f"{i}. {movies.loc[index, 'title']}"
            )

        choice = input(
            "\nEnter movie number: "
        ).strip()

        if choice.isdigit():

            choice = int(choice)

            if 1 <= choice <= min(
                10,
                len(partial_matches)
            ):
                return partial_matches.index[
                    choice - 1
                ]

        return None

    # Fuzzy matching
    titles = movies["search_title"].tolist()

    matches = get_close_matches(
        query,
        titles,
        n=5,
        cutoff=0.6
    )

    if len(matches) > 0:

        print("\nMovie not found exactly.")

        print("\nDid you mean:")

        for i, match in enumerate(
            matches,
            1
        ):

            original_title = movies[
                movies["search_title"] == match
            ]["title"].iloc[0]

            print(
                f"{i}. {original_title}"
            )

        choice = input(
            "\nEnter movie number or 0 to cancel: "
        ).strip()

        if choice.isdigit():

            choice = int(choice)

            if 1 <= choice <= len(matches):

                selected = matches[
                    choice - 1
                ]

                return movies[
                    movies["search_title"] == selected
                ].index[0]

    return None


def recommend_movies(movie_index, n=5):

    print("\nCalculating similarity...")

    # Calculate similarity only for selected movie
    similarity_scores = cosine_similarity(
        tfidf_matrix[movie_index],
        tfidf_matrix
    ).flatten()

    # Get highest similarity scores
    similar_indices = similarity_scores.argsort()[
        ::-1
    ]

    recommendations = []

    for index in similar_indices:

        # Don't recommend the selected movie
        if index == movie_index:
            continue

        title = movies.iloc[index]["title"]

        score = similarity_scores[index]

        recommendations.append(
            (title, score)
        )

        if len(recommendations) == n:
            break

    return recommendations


movie_title = input(
    "Enter movie title: "
)

movie_index = find_movie(movie_title)


if movie_index is None:

    print("\nMovie not selected.")

else:

    selected_title = movies.iloc[
        movie_index
    ]["title"]

    print(
        f"\nSelected Movie: {selected_title}"
    )

    print("\nRecommended Movies:")
    print("-" * 40)

    recommendations = recommend_movies(
        movie_index,
        5
    )

    for i, (title, score) in enumerate(
        recommendations,
        1
    ):

        print(
            f"{i}. {title} "
            f"(Similarity: {score:.4f})"
        )
