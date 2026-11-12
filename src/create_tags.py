from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import ast
import pandas as pd


movies = pd.read_csv(ROOT / "data" / 'feature_movies.csv')


def convert_to_string(value):
    try:
        items = ast.literal_eval(value) if isinstance(value, str) else []
        return " ".join(str(item) for item in items)
    except (ValueError, SyntaxError, TypeError):
        return ""


movies["genres"] = movies["genres"].apply(convert_to_string)
movies["keywords"] = movies["keywords"].apply(convert_to_string)
movies["cast"] = movies["cast"].apply(convert_to_string)
movies["director"] = movies["director"].apply(convert_to_string)

movies["tags"] = (
    movies["overview"].fillna("")
    + " "
    + movies["genres"]
    + " "
    + movies["keywords"]
    + " "
    + movies["cast"]
    + " "
    + movies["director"]
)


movies["tags"] = movies["tags"].str.lower()

movies = movies[
    [
        "id",
        "title",
        "tags",
        "release_date",
        "vote_average",
        "vote_count"
    ]
]


movies.to_csv(ROOT / "data" / 'final_movies.csv', index=False)


print("Tags created successfully!")

if not movies.empty:
    print("\nFirst movie:")
    print("Title:", movies.iloc[0]["title"])
    print("\nTags:")
    print(movies.iloc[0]["tags"])

print("\nFinal dataset shape:", movies.shape)

print("\nFinal dataset saved successfully!")
