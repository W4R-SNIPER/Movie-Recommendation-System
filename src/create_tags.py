import pandas as pd


movies = pd.read_csv("../dataset/feature_movies.csv")


def convert_to_string(value):
    try:
        items = eval(value)
        return " ".join(items)
    except:
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


movies.to_csv("../dataset/final_movies.csv", index=False)


print("Tags created successfully!")

print("\nFirst movie:")
print("Title:", movies.iloc[0]["title"])

print("\nTags:")
print(movies.iloc[0]["tags"])

print("\nFinal dataset shape:", movies.shape)

print("\nFinal dataset saved successfully!")