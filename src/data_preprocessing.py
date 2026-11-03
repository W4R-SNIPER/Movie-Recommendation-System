import pandas as pd

movies = pd.read_csv("../dataset/movies_metadata.csv", low_memory=False)

print("Original dataset shape:", movies.shape)

movies = movies[[
    "id",
    "title",
    "overview",
    "genres",
    "release_date",
    "vote_average",
    "vote_count"
]]

movies = movies.dropna(subset=["id", "title"])

movies["id"] = pd.to_numeric(movies["id"], errors="coerce")

movies = movies.dropna(subset=["id"])

movies["id"] = movies["id"].astype(int)

movies["overview"] = movies["overview"].fillna("")

movies = movies.drop_duplicates(subset=["id"])

print("Cleaned dataset shape:", movies.shape)

print("\nMissing values:")
print(movies.isnull().sum())

print("\nFirst 5 rows:")
print(movies.head())

movies.to_csv("../dataset/clean_movies.csv", index=False)

print("\nClean dataset saved successfully!")