import pandas as pd

movies = pd.read_csv("../dataset/clean_movies.csv")
credits = pd.read_csv("../dataset/credits.csv")
keywords = pd.read_csv("../dataset/keywords.csv")

print("Movies:", movies.shape)
print("Credits:", credits.shape)
print("Keywords:", keywords.shape)

credits = credits[["id", "cast", "crew"]]
keywords = keywords[["id", "keywords"]]

credits["id"] = pd.to_numeric(credits["id"], errors="coerce")
keywords["id"] = pd.to_numeric(keywords["id"], errors="coerce")
movies["id"] = pd.to_numeric(movies["id"], errors="coerce")

credits = credits.dropna(subset=["id"])
keywords = keywords.dropna(subset=["id"])
movies = movies.dropna(subset=["id"])

credits["id"] = credits["id"].astype(int)
keywords["id"] = keywords["id"].astype(int)
movies["id"] = movies["id"].astype(int)

# Remove duplicate IDs before merging
credits = credits.drop_duplicates(subset=["id"])
keywords = keywords.drop_duplicates(subset=["id"])
movies = movies.drop_duplicates(subset=["id"])

print("\nAfter removing duplicate IDs:")
print("Movies:", movies.shape)
print("Credits:", credits.shape)
print("Keywords:", keywords.shape)

# Merge datasets
movies = movies.merge(
    credits,
    on="id",
    how="left"
)

movies = movies.merge(
    keywords,
    on="id",
    how="left"
)

# Remove any duplicate movies created by merging
movies = movies.drop_duplicates(subset=["id"])

print("\nMerged dataset shape:", movies.shape)

print("\nDuplicate IDs:", movies["id"].duplicated().sum())

print("\nColumns:")
print(movies.columns.tolist())

print("\nFirst 5 rows:")
print(
    movies[
        ["id", "title", "genres", "cast", "crew", "keywords"]
    ].head()
)

movies.to_csv(
    "../dataset/merged_movies.csv",
    index=False
)

print("\nMerged dataset saved successfully!")