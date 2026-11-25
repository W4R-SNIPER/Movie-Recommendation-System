from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import pandas as pd
import ast


movies = pd.read_csv(ROOT / "data" / 'merged_movies.csv')


def convert_to_list(value):
    try:
        return [item["name"] for item in ast.literal_eval(value)]
    except (ValueError, SyntaxError, TypeError, KeyError):
        return []


def get_top_cast(value):
    try:
        cast = ast.literal_eval(value)
        return [item["name"] for item in cast[:5]]
    except (ValueError, SyntaxError, TypeError, KeyError):
        return []


def get_director(value):
    try:
        crew = ast.literal_eval(value)

        for item in crew:
            if item["job"] == "Director":
                return [item["name"]]

        return []
    except (ValueError, SyntaxError, TypeError, KeyError):
        return []


movies["genres"] = movies["genres"].fillna("[]")
movies["keywords"] = movies["keywords"].fillna("[]")
movies["cast"] = movies["cast"].fillna("[]")
movies["crew"] = movies["crew"].fillna("[]")
movies["overview"] = movies["overview"].fillna("")


movies["genres"] = movies["genres"].apply(convert_to_list)

movies["keywords"] = movies["keywords"].apply(convert_to_list)

movies["cast"] = movies["cast"].apply(get_top_cast)

movies["director"] = movies["crew"].apply(get_director)


movies = movies[
    [
        "id",
        "title",
        "overview",
        "genres",
        "keywords",
        "cast",
        "director",
        "release_date",
        "vote_average",
        "vote_count"
    ]
]


print("Feature extraction completed!")

if not movies.empty:
    print("\nFirst movie:")
    print("Title:", movies.iloc[0]["title"])
    print("Genres:", movies.iloc[0]["genres"])
    print("Keywords:", movies.iloc[0]["keywords"])
    print("Cast:", movies.iloc[0]["cast"])
    print("Director:", movies.iloc[0]["director"])


movies.to_csv(ROOT / "data" / 'feature_movies.csv', index=False)

print("\nFeature dataset saved successfully!")
print("Shape:", movies.shape)
